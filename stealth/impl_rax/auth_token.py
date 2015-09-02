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
import simplejson as json
from oslo_utils import timeutils

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
