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

        def Success(self, req, resp, project_id):
            return True, None

        def Failure(self, req, resp, project_id):
            return False, "mocking error"

    def setUp(self):
        super(TestRaxAuth, self).setUp()
        self._hdrs = {"X-Auth-Token": self.create_auth_token()}
        self._projid = self.create_project_id()

    @patch('stealth.impl_rax.auth_endpoint.AuthServ.auth', FakeRaxAuth.Success)
    def test_rax_auth_success(self):
        response = self.simulate_get('/auth/' + self._projid,
            headers=self._hdrs)

    @patch('stealth.impl_rax.auth_endpoint.AuthServ.auth', FakeRaxAuth.Failure)
    def test_rax_auth_failure(self):
        response = self.simulate_get('/auth/' + self._projid,
            headers=self._hdrs)

    '''
    def test_error_returns(self):
        from deucecnc.model import List

        with patch.object(List, 'listing', return_value=None):
            response = self.simulate_get('/list'.
                format(self._projid), headers=self._hdrs)
            self.assertEqual(self.srmock.status, falcon.HTTP_500)
    '''
