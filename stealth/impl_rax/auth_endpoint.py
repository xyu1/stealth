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

from stealth.impl_rax.auth_token import AdminToken
from stealth.impl_rax import token_validation


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

            valid, auth_token = token_validation.validate_client_token(
                self.redis_client,
                self.auth_url, project_id, cache_key)

            if not valid:
                valid, usertoken, cache_key =\
                    token_validation.validate_client_impersonation(
                        self.redis_client, self.auth_url, project_id,
                        self.Admintoken)

                if not valid:
                    # Validation failed for some reason,
                    # just error out as a 401
                    LOG.error('Auth Token validation failed.')
                    return False, 'Auth Token validation failed.'

                # WHY NOT? else if usertoken and usertoken['token']:
                auth_token = usertoken['token']

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
            return True, cache_key

        except (KeyError, LookupError):
            # Header failure, error out with 412
            LOG.error('Missing required headers.')
            return False, 'Missing required headers.'
