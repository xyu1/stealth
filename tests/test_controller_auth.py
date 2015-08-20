import json

import falcon

from tests import V1Base
from mock import patch
from stealth.transport.wsgi import errors


class TestAuth(V1Base):
    def setUp(self):
        super(TestAuth, self).setUp()
        self._hdrs = {"X-Auth-Token": self.create_auth_token()}
        self._projid = self.create_project_id()

    def test_auth(self):
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
