#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
#
# See the License for the specific language governing permissions and
# limitations under the License.

import functools
import datetime
import stealth.util.log as logging
import pytz
import dateutil
import dateutil.parser
from abc import ABCMeta, abstractmethod, abstractproperty
import requests
from keystoneclient import exceptions
import msgpack
import redis
from redis import connection
import simplejson as json
from stealth import conf
from oslo_utils import timeutils
import hmac
import hashlib
import base64
from stealth.impl_rax.auth_token import UserToken, TokenBase

STALE_TOKEN_DURATION = 30
LOG = logging.getLogger(__name__)


class InvalidKeystoneClient(Exception):
    pass


class InvalidAccessInformation(Exception):
    pass


class UnknownAuthenticationDataVersion(Exception):
    pass


def get_auth_redis_client():
    """Get a Redis Client connection from the pool

    uses the cnc:auth_redis settings
    """

    if conf.auth_redis.ssl_enable != 'None':
        pool = redis.ConnectionPool(
            host=conf.auth_redis.host,
            port=conf.auth_redis.port,
            db=conf.auth_redis.redis_db,
            password=conf.auth_redis.password,
            ssl_keyfile=conf.auth_redis.ssl_keyfile,
            ssl_certfile=conf.auth_redis.ssl_certfile,
            ssl_cert_reqs=conf.auth_redis.ssl_cert_reqs,
            ssl_ca_certs=conf.auth_redis.ssl_ca_certs,
            connection_class=connection.SSLConnection)
    else:
        pool = redis.ConnectionPool(host=conf.auth_redis.host,
                                    port=conf.auth_redis.port,
                                    db=conf.auth_redis.redis_db)

    return redis.Redis(connection_pool=pool)


def _generate_cache_key(t):
    """Convert a tuple to a cache key."""
    hashval = hmac.new('A_SECRET_KEY'.encode(), t.encode(),
        hashlib.sha256).hexdigest()
    return hashval


def _send_data_to_cache(redis_client, url, token_data):
    """Stores the authentication data to cache

    :param redis_client: redis.Redis object connected to the redis cache
    :param url: URL used for authentication
    :param token_data: json formatted token information to cache.

    :returns: True and cache_key on success, otherwise False and None
    """
    try:
        # Convert the storable format
        cache_data = json.dumps(token_data.token_data, sort_keys=True)

        # Build the cache key and store the value
        # Use the token's expiration time for the cache expiration
        cache_key = _generate_cache_key(cache_data)

        redis_client.set(cache_key, cache_data)
        redis_client.pexpireat(cache_key, token_data.expires_norm)

        return True, cache_key

    except Exception as ex:
        msg = ('Endpoint: Failed to cache the data - Exception: \
            %(s_except)s') % {
            's_except': str(ex),
        }
        LOG.error(msg)
        return False, None


def _retrieve_data_from_cache(redis_client, url, tenant, cache_key):
    """Retrieve the authentication data from cache

    :param redis_client: redis.Redis object connected to the redis cache
    :param url: URL used for authentication
    :param tenant: tenant id of the user
    :param cache_key: client side auth_token for the tenant_id

    :returns: cached user info on success, or None
    """
    if cache_key is None:
        return None

    cached_data = None
    try:
        # Look up the token from the cache
        cached_data = redis_client.get(cache_key)

    except Exception:
        LOG.debug(('Failed to retrieve data to cache for key %(s_key)s') % {
            's_key': cache_key
        })
        return None

    if cached_data is not None:
        # So 'data' can be used in the exception handler...
        data = None

        try:
            return json.loads(cached_data)

        except Exception as ex:
            # The cached object didn't match what we expected
            msg = ('Endpoint: Stored Data does not contain any credentials - '
                'Exception: %(s_except)s; Data: $(s_data)s') % {
                's_except': str(ex),
                's_data': str(cached_data)
            }
            LOG.error(msg)
            return None
    else:
        LOG.debug(('No data in cache for key %(s_key)s') % {
            's_key': cache_key
        })
        # It wasn't cached
        return None


def _validate_client_token(redis_client, url, tenant, cache_key):
    """Validate Input Client Token

    :param redis_client: redis.Redis object connected to the redis cache
    :param url: Keystone Identity URL to authenticate against
    :param tenant: tenant id of user data to retrieve
    :param cache_key: client side auth_token for the tenant_id

    :returns: True and token-data on success, False and None otherwise
    """

    try:
        # Try to get the client's access infomration from cache
        token_data = _retrieve_data_from_cache(redis_client,
                url, tenant, cache_key)
        if token_data is not None:
            norm = TokenBase.normal_time(token_data['expires'])
            if TokenBase.will_expire_soon(TokenBase.
                    normal_time(token_data['expires'])):
                LOG.info('Token has expired')
            else:
                return True, token_data['token']

        LOG.debug(('Unable to get Access information for '
            '%(s_tenant)s') % {
            's_tenant': tenant
        })
        return False, None

    except Exception as ex:
        msg = ('Endpoint: Error while trying to authenticate against'
            ' %(s_url)s - %(s_except)s') % {
            's_url': url,
            's_except': str(ex)
        }
        LOG.debug(msg)
        return False, None


def _validate_client_impersonation(redis_client, url, tenant, admintoken):
    """Validate Client Token

    :param redis_client: redis.Redis object connected to the redis cache
    :param url: Keystone Identity URL to authenticate against
    :param admintoken: admin token object for Keystone Identity authentication
    :param tenant: tenant id of user data to retrieve

    :returns: True and the auth token on success, otherwise False and None
    """

    try:
        user_token = UserToken(url=url, tenant=tenant, admintoken=admintoken)
        if user_token.token_data is None:
            LOG.debug(('Unable to get Access information for '
                '%(s_tenant)s') % {
                's_tenant': tenant
            })
            return False, None, None

        # cache the data so it is easier to access next time
        retval, cache_key = _send_data_to_cache(redis_client,
            url=url, token_data=user_token)

        return True, user_token.token_data, cache_key

    except Exception as ex:
        msg = ('Endpoint: Error while trying to authenticate against'
            ' %(s_url)s - %(s_except)s') % {
            's_url': url,
            's_except': str(ex)
        }
        LOG.debug(msg)
        return False, None, None
