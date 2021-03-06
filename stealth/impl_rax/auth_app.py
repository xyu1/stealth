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

#
# Module can be simply actived as a uWsgi service app.
# Example is in bin/authserv
#


import falcon
from stealth.impl_rax.auth_token import AdminToken
from stealth.impl_rax import token_validation
from stealth import conf

import stealth.util.log as logging

LOG = logging.getLogger(__name__)


def _http_precondition_failed(start_response):
    """Responds with HTTP 412."""
    start_response(falcon.HTTP_412, [('Content-Length', '0')])
    return []


def _http_unauthorized(start_response):
    """Responds with HTTP 401."""
    start_response(falcon.HTTP_401, [('Content-Length', '0')])
    return []


def app(redis_client, auth_url=None, admin_name=None, admin_pass=None):
    """
    uWSGI app for returning impersonation token.

    :param redis_client: redis.Redis object connected to the redis cache
    """
    if auth_url is None:
        auth_url = conf.auth.auth_url
    if admin_name is None:
        admin_name = conf.auth.admin_name
    if admin_pass is None:
        admin_pass = conf.auth.admin_pass
    Admintoken = AdminToken(auth_url, admin_name, admin_pass)

    LOG.debug('App: Auth URL: {0:}'.format(auth_url))

    def auth(env, start_response):
        try:
            project_id = env['HTTP_X_PROJECT_ID']
            token = ''
            cache_key = ''
            valid = False

            if 'HTTP_X_AUTH_TOKEN' in env:
                cache_key = env['HTTP_X_AUTH_TOKEN']

            valid, token = token_validation.validate_client_token(redis_client,
                auth_url, project_id, cache_key)
            if valid:
                LOG.debug(('App: Auth Token validated.'))
                start_response('204 No Content',
                    [])
                return []

            # validate the client and fill out the env
            valid, usertoken, cache_key = \
                token_validation.validate_client_impersonation(
                    redis_client, auth_url, project_id, Admintoken)
            if valid and usertoken and usertoken['token']:
                token = usertoken['token']
                # env['X-AUTH-TOKEN'] = token
                LOG.debug(('App: Auth Token validated.'))
                start_response('204 No Content',
                    [('X-AUTH-TOKEN', cache_key)])
                return []

            # Validation failed. Error out as a 401
            LOG.error(('App: Auth Token validation failed.'))
            return _http_unauthorized(start_response)

        except (KeyError, LookupError):
            # Header failure, error out with 412
            LOG.error(('App: Missing required headers.'))
            return _http_precondition_failed(start_response)

    return auth
