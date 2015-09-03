from unittest import TestCase
from stealth.impl_rax import auth_middleware
from stealth.impl_rax import auth_token_cache


def start_response(status, headers):
    return []


def example_app(env, start_response):
    start_response('204 No Content', [])
    return []


def side_effect_exception(*args):
    raise Exception('mock exception')


class TestAuthMiddleware(TestCase):

    def setUp(self):
        super(TestAuthMiddleware, self).setUp()
        self.auth_redis_client = auth_token_cache.get_auth_redis_client()
        self.app = auth_middleware.wrap(example_app, self.auth_redis_client)

    def test_middleware(self):
        env = dict()
        self.app(env, start_response)

        # response = self.simulate_get('/', headers={})
        # self.assertEqual(self.srmock.status, falcon.HTTP_404)

        # response = self.simulate_get('/',
        #                             headers={'x-project-id':
        #                                      self.create_project_id()})
        # self.assertEqual(self.srmock.status, falcon.HTTP_404)
