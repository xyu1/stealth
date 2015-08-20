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
from stealth.impl_rax.auth_endpoint import AdminToken, \
    LOG, _validate_client_impersonation, _validate_client_token
from stealth import conf


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
            if 'HTTP_X_PROJECT_ID' in env:
                project_id = env['HTTP_X_PROJECT_ID']
            else:
                project_id = env['PATH_INFO'][env['PATH_INFO'].rfind('/') + 1:]
            token = ''
            valid = False

            if 'HTTP_X_AUTH_TOKEN' in env:
                token = env['HTTP_X_AUTH_TOKEN']

            valid, token = _validate_client_token(redis_client,
                auth_url, project_id, token)

            if not valid:
                valid, Usertoken = _validate_client_impersonation(redis_client,
                    auth_url, project_id, Admintoken)
                if valid and Usertoken and Usertoken['token']:
                    token = Usertoken['token']
                    env['HTTP_X_AUTH_TOKEN'] = token

            # validate the client and fill out the environment it's valid
            if valid:
                LOG.debug(('App: Auth Token validated.'))
                start_response('204 No Content',
                    [('X-AUTH-TOKEN', token)])
                return []

            else:
                # Validation failed for some reason, just error out as a 401
                LOG.error(('App: Auth Token validation failed.'))
                return _http_unauthorized(start_response)
        except (KeyError, LookupError):
            # Header failure, error out with 412
            LOG.error(('App: Missing required headers.'))
            return _http_precondition_failed(start_response)

    return auth
