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

from unittest import TestCase
import mock
import requests_mock
from stealth import conf
from falcon import testing as ftest


class Simu_Request(object):

    def simulate_request(self, app, srmock, path, **kwargs):
        """Simulate a request.

        Simulates a WSGI request to the API for testing.

        :param path: Request path for the desired resource
        :param kwargs: Same as falcon.testing.create_environ()

        :returns: standard WSGI iterable response
        """

        headers = dict()
        headers = kwargs.get('headers', headers).copy()
        kwargs['headers'] = headers
        return app(ftest.create_environ(path=path, **kwargs),
            srmock)

    def simulate_get(self, app, srmock, *args, **kwargs):
        """Simulate a GET request."""
        kwargs['method'] = 'GET'
        return self.simulate_request(app, srmock, *args, **kwargs)

    def simulate_post(self, app, srmock, *args, **kwargs):
        """Simulate a POST request."""
        kwargs['method'] = 'POST'
        return self.simulate_request(app, srmock, *args, **kwargs)


def start_response(status, headers):
    return []


def example_app(env, start_response):
    start_response('204 No Content', [])
    return []


def side_effect_validate_client_token(*args):
    return True, 'validated-token'


def side_effect_validate_client_impersonation(*args):
    return True, dict({'token': 'validated-token'}), 'cache_key'


class TestAuthMiddleware(TestCase):

    def setUp(self):
        super(TestAuthMiddleware, self).setUp()
        self.headers = {}
        self.srmock = ftest.StartResponseMock()

    @requests_mock.mock()
    def test_middleware(self, m):
        simu_req = Simu_Request()
        from stealth.impl_rax import auth_middleware
        import stealth.impl_rax.token_validation
        env = dict()
        m.post('http://mockurl/tokens', text='{"access": \
            {"token": {"id": "the-token", "expires": \
            "2025-09-04T14:09:20.236Z"}}}')
        conf.auth.auth_url = 'http://mockurl'
        self.auth_redis_client = \
            stealth.impl_rax.token_validation.get_auth_redis_client()
        self.assertIsNotNone(self.auth_redis_client)
        self.app = auth_middleware.wrap(example_app, self.auth_redis_client)
        self.app(env, start_response)

        response = simu_req.simulate_get(self.app, self.srmock, '/', headers={
            'X-PROJECT-ID': 'proj12345'})
        self.assertEqual(response, [])

        response = simu_req.simulate_get(self.app,
            self.srmock, '/', headers={'X-PROJECT-ID': 'proj12345',
            'X-AUTH-TOKEN': 'token12345'})
        self.assertEqual(response, [])

        with mock.patch.object(stealth.impl_rax.token_validation,
                'validate_client_token',
                side_effect=side_effect_validate_client_token):
            response = simu_req.simulate_get(self.app,
                self.srmock, '/', headers={
                    'X-PROJECT-ID': 'proj12345',
                    'X-AUTH-TOKEN': 'token12345'})
            self.assertEqual(response, [])

        with mock.patch.object(stealth.impl_rax.token_validation,
                'validate_client_impersonation',
                side_effect=side_effect_validate_client_impersonation):
            response = simu_req.simulate_get(self.app,
                self.srmock, '/', headers={
                    'X-PROJECT-ID': 'proj12345',
                    'X-AUTH-TOKEN': 'token12345'})
            self.assertEqual(response, [])
