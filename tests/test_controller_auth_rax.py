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

import json

import falcon

from tests import V1Base
from mock import patch


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
        self.assertEqual(response, [])

    @patch('stealth.impl_rax.auth_endpoint.AuthServ.auth', FakeRaxAuth.Failure)
    def test_rax_auth_failure(self):
        hdrs = self._hdrs.copy()
        response = self.simulate_get('/auth',
            headers=hdrs)
        self.assertEqual(json.loads(response[0].decode('ascii'))
            ['description'], "Missing required headers.")
        hdrs['X-PROJECT-ID'] = self._projid
        response = self.simulate_get('/auth',
            headers=hdrs)
        self.assertEqual(json.loads(response[0].decode('ascii'))
            ['description'], "mocking error")
