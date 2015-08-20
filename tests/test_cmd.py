from unittest import TestCase
from stealth.transport.wsgi.driver import Driver
import stealth.cmd.server
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


class TestCmd(TestCase):

    def setUp(self):
        super(TestCmd, self).setUp()

    def tearDown(self):
        super(TestCmd, self).tearDown()

    @patch('stealth.transport.wsgi.driver.Driver.listen', FakeDriver.listen)
    def test_server1(self):
        stealth.cmd.server.run()

    @patch('stealth.transport.wsgi.driver.Driver.listen',
          FakeDriver.listenInterrupt)
    def test_server2(self):
        stealth.cmd.server.run()

    @patch('stealth.transport.wsgi.driver.Driver.listen',
          FakeDriver.listenExcept)
    def test_server3(self):
        with self.assertRaises(SystemExit):
            with self.assertRaises(Exception):
                stealth.cmd.server.run()
