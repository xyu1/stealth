#
# Copyright (c) 2015 Xuan Yu xuanyu1@gmail.com
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
# See the License for the specific language governing permissions and
# limitations under the License.

import logging
import falcon
# Load Rackspace version of auth endpoint.
import stealth.impl_rax.auth_endpoint as auth
from stealth.impl_rax import token_validation
import stealth.util.log as logging
from stealth.transport.wsgi import errors
from stealth import conf
LOG = logging.getLogger(__name__)


# Get the separated Redis Server for Auth
auth_redis_client = token_validation.get_auth_redis_client()

authserv = auth.AuthServ(auth_redis_client)


class ItemResource(object):

    def on_get(self, req, resp):
        try:
            project_id = req.headers['X-PROJECT-ID']
            LOG.info('Auth [{0}]... '.format(project_id))
            res, msg = authserv.auth(req, resp)
            if res is False:
                raise errors.HTTPUnauthorizedError(msg)
            else:
                resp.location = '/auth/%s' % (project_id)
            resp.status = falcon.HTTP_204  # This is the default status
            resp.set_header('X-AUTH-TOKEN', msg)
        except (KeyError, LookupError):
            # Header failure, error out with 412
            LOG.error('Missing required headers.')
            raise errors.HTTPBadRequestBody("Missing required headers.")
