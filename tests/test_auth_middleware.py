from unittest import TestCase
import mock
import requests_mock
from stealth import conf
from falcon import testing as ftest


def start_response(status, headers):
    return []


def example_app(env, start_response):
    start_response('204 No Content', [])
    return []


def side_effect_exception(*args):
    raise Exception('mock exception')


def side_effect_validate_client_token(*args):
    return True, 'validated-token'


def side_effect_validate_client_impersonation(*args):
    return True, dict({'token': 'validated-token'}), 'cache_key'


class TestAuthMiddleware(TestCase):

    def setUp(self):
        super(TestAuthMiddleware, self).setUp()
        self.headers = {}
        self.srmock = ftest.StartResponseMock()

    def simulate_request(self, path, **kwargs):
        """Simulate a request.

        Simulates a WSGI request to the API for testing.

        :param path: Request path for the desired resource
        :param kwargs: Same as falcon.testing.create_environ()

        :returns: standard WSGI iterable response
        """

        headers = kwargs.get('headers', self.headers).copy()
        kwargs['headers'] = headers
        return self.app(ftest.create_environ(path=path, **kwargs),
                        self.srmock)

    def simulate_get(self, *args, **kwargs):
        """Simulate a GET request."""
        kwargs['method'] = 'GET'
        return self.simulate_request(*args, **kwargs)

    def simulate_head(self, *args, **kwargs):
        """Simulate a HEAD request."""
        kwargs['method'] = 'HEAD'
        return self.simulate_request(*args, **kwargs)

    def simulate_put(self, *args, **kwargs):
        """Simulate a PUT request."""
        kwargs['method'] = 'PUT'
        return self.simulate_request(*args, **kwargs)

    def simulate_post(self, *args, **kwargs):
        """Simulate a POST request."""
        kwargs['method'] = 'POST'
        return self.simulate_request(*args, **kwargs)

    def simulate_delete(self, *args, **kwargs):
        """Simulate a DELETE request."""
        kwargs['method'] = 'DELETE'
        return self.simulate_request(*args, **kwargs)

    def simulate_patch(self, *args, **kwargs):
        """Simulate a PATCH request."""
        kwargs['method'] = 'PATCH'
        return self.simulate_request(*args, **kwargs)

    @requests_mock.mock()
    def test_middleware(self, m):
        from stealth.impl_rax import auth_middleware
        import stealth.impl_rax.auth_token_cache
        env = dict()
        m.post('http://mockurl/tokens', text='{"access": \
            {"token": {"id": "the-token", "expires": \
            "2025-09-04T14:09:20.236Z"}}}')
        conf.auth.auth_url = 'http://mockurl'
        self.auth_redis_client = \
            stealth.impl_rax.auth_token_cache.get_auth_redis_client()
        self.app = auth_middleware.wrap(example_app, self.auth_redis_client)
        self.app(env, start_response)

        response = self.simulate_get('/', headers={
            'X-PROJECT-ID': 'proj12345'})

        response = self.simulate_get('/', headers={'X-PROJECT-ID': 'proj12345',
            'X-AUTH-TOKEN': 'token12345'})

        with mock.patch.object(stealth.impl_rax.auth_token_cache,
                'validate_client_token',
                side_effect=side_effect_validate_client_token):
            response = self.simulate_get('/', headers={
                'X-PROJECT-ID': 'proj12345',
                'X-AUTH-TOKEN': 'token12345'})

        with mock.patch.object(stealth.impl_rax.auth_token_cache,
                'validate_client_impersonation',
                side_effect=side_effect_validate_client_impersonation):
            response = self.simulate_get('/', headers={
                'X-PROJECT-ID': 'proj12345',
                'X-AUTH-TOKEN': 'token12345'})
