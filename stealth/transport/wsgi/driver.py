from wsgiref import simple_server

import falcon

from stealth.transport.wsgi import v1_0
import stealth.util.log as logging
from stealth import conf


class Driver(object):

    def __init__(self):
        self.app = None
        self._init_routes()

    def _init_routes(self):
        """Initialize URI routes to resources."""

        endpoints = [
            ('', v1_0.public_endpoints()),

        ]

        self.app = falcon.API()

        for version_path, endpoints in endpoints:
            for route, resource in endpoints:
                self.app.add_route(version_path + route, resource)

    def listen(self):
        """Self-host using 'bind' and 'port' from conf"""
        msgtmpl = (u'Serving on host %(bind)s:%(port)s')
        logger = logging.getLogger(__name__)
        logger.info(msgtmpl,
                    {'bind': conf.server.host, 'port': conf.server.port})

        httpd = simple_server.make_server(conf.server.host,
                                          conf.server.port,
                                          self.app)
        httpd.serve_forever()
