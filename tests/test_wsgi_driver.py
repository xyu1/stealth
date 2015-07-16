from unittest import TestCase

from mock import patch
from wsgiref import simple_server

from stealth.transport.wsgi.driver import Driver
import stealth.util.log as logging


class TestDriver(TestCase):

    def test_driver(self):
        class MockServer(object):

            def serve_forever(self):
                LOG = logging.getLogger(__name__)
                LOG.info("Mock Server - Started")

        mock_server_object = MockServer()
        with patch.object(simple_server,
                          'make_server',
                          return_value=mock_server_object):
            app_container = Driver()
            app_container.listen()
