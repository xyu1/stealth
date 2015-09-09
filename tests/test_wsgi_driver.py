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

from mock import patch
from wsgiref import simple_server

import stealth.util.log as logging

from tests import V1Base


class TestDriver(V1Base):

    def test_driver(self):
        class MockServer(object):

            def serve_forever(self):
                LOG = logging.getLogger(__name__)
                LOG.info("Mock Server - Started")

        mock_server_object = MockServer()
        from stealth.transport.wsgi.driver import Driver
        with patch.object(simple_server,
                          'make_server',
                          return_value=mock_server_object):
            app_container = Driver()
            app_container.listen()
