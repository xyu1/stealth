from tests import V1Base
import requests_mock


def start_response(status, headers):
    return []


def example_app(env, start_response):
    start_response('204 No Content', [])
    return []


def side_effect_exception(*args):
    raise Exception('mock exception')


class TestAuthMiddleware(V1Base):

    def setUp(self):
        super(TestAuthMiddleware, self).setUp()

    @requests_mock.mock()
    def test_middleware(self, m):
        from stealth.impl_rax import auth_middleware
        from stealth.impl_rax import auth_token_cache
        env = dict()
        m.post('http://mockurl/tokens', text='{"access": \
            {"token": {"id": "the-token", "expires": \
            "2025-09-04T14:09:20.236Z"}}}')
        self.auth_redis_client = auth_token_cache.get_auth_redis_client()
        self.app = auth_middleware.wrap(example_app, self.auth_redis_client)
        self.app(env, start_response)

        # response = self.simulate_get('/', headers={})
        # self.assertEqual(self.srmock.status, falcon.HTTP_404)

        # response = self.simulate_get('/',
        #                             headers={'x-project-id':
        #                                      self.create_project_id()})
        # self.assertEqual(self.srmock.status, falcon.HTTP_404)
