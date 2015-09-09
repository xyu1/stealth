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

from tests import V1Base
from mock import patch


# Monkey patch the Driver
class FakeDriver(object):
    def __init__(self):
        pass

    def listen(self):
        return

    def listenExcept(self):
        raise Exception

    def listenInterrupt(self):
        raise KeyboardInterrupt


class TestCmd(V1Base):

    def setUp(self):
        super(TestCmd, self).setUp()

    def tearDown(self):
        super(TestCmd, self).tearDown()

    @patch('stealth.transport.wsgi.driver.Driver.listen', FakeDriver.listen)
    def test_server1(self):
        import stealth.cmd.server
        stealth.cmd.server.run()

    @patch('stealth.transport.wsgi.driver.Driver.listen',
          FakeDriver.listenInterrupt)
    def test_server2(self):
        import stealth.cmd.server
        stealth.cmd.server.run()

    @patch('stealth.transport.wsgi.driver.Driver.listen',
          FakeDriver.listenExcept)
    def test_server3(self):
        import stealth.cmd.server
        with self.assertRaises(SystemExit):
            with self.assertRaises(Exception):
                stealth.cmd.server.run()
