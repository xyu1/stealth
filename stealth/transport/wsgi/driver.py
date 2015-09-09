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

from wsgiref import simple_server

import falcon

from stealth.transport.wsgi import v1_0
from stealth.transport.wsgi import hooks
import stealth.util.log as logging
from stealth import conf

LOG = logging.getLogger(__name__)


class Driver(object):

    def __init__(self):
        self.app = None
        self._init_routes()

    def before_hooks(self, req, resp, params):

        # Disk + Sqlite

        return [
            hooks.ContextHook(req, resp, params),
            hooks.TransactionidHook(req, resp, params)
        ]

    def _init_routes(self):
        """Initialize URI routes to resources."""

        endpoints = [
            ('', v1_0.public_endpoints()),

        ]

        self.app = falcon.API(before=self.before_hooks)

        for version_path, endpoints in endpoints:
            for route, resource in endpoints:
                self.app.add_route(version_path + route, resource)

    def listen(self):
        """Self-host using 'bind' and 'port' from conf"""
        msgtmpl = (u'Serving on host %(bind)s:%(port)s')
        LOG.info(msgtmpl,
            {'bind': conf.server.host, 'port': conf.server.port})

        httpd = simple_server.make_server(conf.server.host,
                                          conf.server.port,
                                          self.app)
        httpd.serve_forever()
