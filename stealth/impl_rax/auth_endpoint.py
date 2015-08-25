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

STALE_TOKEN_DURATION = 30
LOG = logging.getLogger(__name__)


class TokenBase(object):

    def __init__(self, url, tenant, token=None):
        self.auth_url = url
        self._tenant = tenant
        self._token = token
        self._expires = str(timeutils.utcnow())
        self._norm_expires = self.normal_time(self._expires)
        if tenant and token is None:
            self._update_token()

    @abstractmethod
    def _update_token(self):
        raise NotImplementedError

    @staticmethod
    def normal_time(timestr):
        expires = dateutil.parser.parse(timestr)
        if expires.tzinfo is None:
            expires = pytz.timezone('UTC').localize(
                dateutil.parser.parse(timestr))

        return expires

    @staticmethod
    def will_expire_soon(expires, stale_duration=None):
        stale_duration = (STALE_TOKEN_DURATION if stale_duration is None
                          else stale_duration)
        soon = pytz.timezone('UTC').localize(timeutils.utcnow() +
            datetime.timedelta(seconds=stale_duration))
        return expires < soon

    @property
    def token(self):
        if self._token is None:
            return None
        if self.will_expire_soon(self._norm_expires):
            self._update_token()
        return self._token

    @property
    def expires(self):
        return self._expires

    @property
    def expires_norm(self):
        return self._norm_expires

    @property
    def tenant(self):
        return self._tenant

    @property
    def token_data(self):
        if self._token is None:
            return None
        if self.will_expire_soon(self._norm_expires):
            self._update_token()
        return {'token': self._token, 'tenant': self._tenant,
            'expires': self._expires}


class AdminToken(TokenBase):

    def __init__(self, url, tenant, passwd, token=None):
        self._passwd = passwd
        super(AdminToken, self).__init__(url=url, tenant=tenant, token=token)

    def _update_token(self):
        urlpath = '{0}/tokens'.format(self.auth_url)
        headers = {}
        headers['Content-type'] = 'application/json'
        data = '{"auth":{"passwordCredentials":{"username":"%s",\
            "password":"%s"}}}' % (self._tenant, self._passwd)
        res = requests.post(urlpath, headers=headers, data=data)
        if res.status_code != 200:
            raise exceptions.AuthorizationFailure
        self._token = res.json()['access']['token']['id']
        self._expires = res.json()['access']['token']['expires']
        self._norm_expires = self.normal_time(self._expires)


class UserToken(TokenBase):

    def __init__(self, url, tenant, Admintoken, token=None):
        self._Admintoken = Admintoken
        super(UserToken, self).__init__(url=url, tenant=tenant, token=token)

    def _update_token(self):

        try:
            # Step 1. List users of the tenant
            urlpath = '{0}/tenants/{1}/users'.format(
                self.auth_url, self._tenant)
            headers = {}
            headers['X-Auth-Token'] = self._Admintoken.token
            res = requests.get(urlpath, headers=headers)
            if res.status_code != 200:
                raise exceptions.AuthorizationFailure
            userid = res.json()['users'][0]['id']

            # Step 2. Lookup the admin role user id of the tenant
            urlpath = '{0}/users/{1}/RAX-AUTH/admins'.format(
                self.auth_url, userid)
            res = requests.get(urlpath, headers=headers)
            if res.status_code != 200:
                raise exceptions.AuthorizationFailure
            username = res.json()['users'][0]['username']

            # Step 3. Create the impersonation token for the user
            urlpath = '{0}/RAX-AUTH/impersonation-tokens'.format(self.auth_url)
            headers['Content-Type'] = 'application/json'
            data = '{"RAX-AUTH:impersonation": {"user": {"username":"%s"}, \
                "expire-in-seconds": 10800}}' % (username)
            res = requests.post(urlpath, headers=headers, data=data)
            if res.status_code != 200:
                raise exceptions.AuthorizationFailure
            self._token = res.json()['access']['token']['id']
            self._expires = res.json()['access']['token']['expires']
            self._norm_expires = self.normal_time(self._expires)
        except (exceptions.AuthorizationFailure,
                exceptions.Unauthorized) as ex:
            # Provided data was invalid and authorization failed
            msg = ('Endpoint: Failed to authenticate against %(s_url)s'
                ' - %(s_except)s') % {
                's_url': self.auth_url,
                's_except': str(ex)
            }
            LOG.debug(msg)
            self._token = None
            self._expires = None
        except Exception as ex:
            # Provided data was invalid or something else went wrong
            msg = ('Endpoint: Failed to authenticate against %(s_url)s'
                ' - %(s_except)s') % {
                's_url': self.auth_url,
                's_except': str(ex)
            }
            LOG.debug(msg)
            self._token = None
            self._expires = None


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

    :returns: True on success, otherwise False
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
                's_data': data
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


def _validate_client_impersonation(redis_client, url, tenant, Admintoken):
    """Validate Client Token

    :param redis_client: redis.Redis object connected to the redis cache
    :param url: Keystone Identity URL to authenticate against
    :param Admintoken: admin token object for Keystone Identity authentication
    :param tenant: tenant id of user data to retrieve

    :returns: True and the auth token on success, otherwise False and None
    """

    try:
        user_token = UserToken(url=url, tenant=tenant, Admintoken=Admintoken)
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


class AuthServ(object):

    def __init__(self, redis_client, auth_url=None,
          admin_name=None, admin_pass=None):

        self.redis_client = redis_client
        if auth_url is None:
            self.auth_url = conf.auth.auth_url
        else:
            self.auth_url = auth_url
        if admin_name is None:
            admin_name = conf.auth.admin_name
        else:
            amdin_name = admin_name
        if admin_pass is None:
            admin_pass = conf.auth.admin_pass
        else:
            admin_pass = admin_pass
        LOG.debug('Auth URL: {0:}'.format(self.auth_url))
        self.Admintoken = AdminToken(self.auth_url, admin_name, admin_pass)

    def auth(self, req, resp):

        try:
            auth_token = None
            valid = False
            cache_key = None

            project_id = req.headers['X-PROJECT-ID']

            if 'X-AUTH-TOKEN' in req.headers:
                cache_key = req.headers['X-AUTH-TOKEN']

            valid, auth_token = _validate_client_token(self.redis_client,
                self.auth_url, project_id, cache_key)

            if not valid:
                valid, Usertoken, cache_key = _validate_client_impersonation(
                    self.redis_client, self.auth_url, project_id,
                    self.Admintoken)

                if not valid:
                    # Validation failed for some reason,
                    # just error out as a 401
                    LOG.error('Auth Token validation failed.')
                    return False, 'Auth Token validation failed.'

                # WHY NOT? else if Usertoken and Usertoken['token']:
                auth_token = Usertoken['token']

            #
            # auth_token here is the real auth token from Keystone,
            # It can be replaced in the user requests and forward
            # to the service providers.
            #
            # req.headers['X-AUTH-TOKEN'] = auth_token
            #

            # validate the client and fill out the request it's valid
            LOG.debug('Auth Token validated.')
            # Return only generated hmac values back to the users.
            return True, auth_token

        except (KeyError, LookupError):
            # Header failure, error out with 412
            LOG.error('Missing required headers.')
            return False, 'Missing required headers.'
