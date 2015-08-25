import json

import falcon

from tests import V1Base
from mock import patch
from stealth.transport.wsgi import errors
import stealth.impl_rax.auth_endpoint as auth


class TestRaxAuth(V1Base):
    # Monkey patch the AUTH
    class FakeRaxAuth(object):
        def __init__(self):
            pass

        def Success(self, req, resp):
            return True, None

        def Failure(self, req, resp):
            return False, "mocking error"

    def setUp(self):
        super(TestRaxAuth, self).setUp()
        self._hdrs = {"X-Auth-Token": self.create_auth_token()}
        self._projid = self.create_project_id()

    @patch('stealth.impl_rax.auth_endpoint.AuthServ.auth', FakeRaxAuth.Success)
    def test_rax_auth_success(self):
        hdrs = self._hdrs.copy()
        hdrs['X-PROJECT-ID'] = self._projid
        response = self.simulate_get('/auth',
            headers=hdrs)

    @patch('stealth.impl_rax.auth_endpoint.AuthServ.auth', FakeRaxAuth.Failure)
    def test_rax_auth_failure(self):
        hdrs = self._hdrs.copy()
        response = self.simulate_get('/auth',
            headers=hdrs)
        hdrs['X-PROJECT-ID'] = self._projid
        response = self.simulate_get('/auth',
            headers=hdrs)
