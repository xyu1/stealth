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

import stealth.util.log as logging
import redis
from redis import connection
from stealth import conf
from stealth.impl_rax.auth_token import UserToken, TokenBase
from stealth.impl_rax.auth_token_cache import _send_data_to_cache, \
    _retrieve_data_from_cache

LOG = logging.getLogger(__name__)


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


def validate_client_token(redis_client, url, tenant, cache_key):
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


def validate_client_impersonation(redis_client, url, tenant, admintoken):
    """Validate Client Token

    :param redis_client: redis.Redis object connected to the redis cache
    :param url: Keystone Identity URL to authenticate against
    :param admintoken: admin token object for Keystone Identity authentication
    :param tenant: tenant id of user data to retrieve

    :returns: True and the auth token on success, otherwise False and None
    """

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
