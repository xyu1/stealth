from unittest import TestCase
from stealth.impl_rax.auth_token import AdminToken, UserToken
# Mock requests
import requests
import requests_mock


def side_effect_exception(*args):
    raise Exception('mock exception')


def side_effect_redis_getdata(*args):
    return '{"token": "the-token", "tenant": "tenant-id", \
        "expires": "2025-09-04T14:09:20.236Z"}'


def side_effect_redis_getdata_wrong(*args):
    return '{"token": "the-token"}, "tenant": "tenant-id", \
        "expires": "2025-09-04T14:09:20.236Z"}'


def side_effect_redis_getdata_expired(*args):
    return '{"token": "the-token", "tenant": "tenant-id", \
        "expires": "1025-09-04T14:09:20.236Z"}'


class TestAuthToken(TestCase):

    @requests_mock.mock()
    def test_admin_token(self, m):
        token = AdminToken(url='http://mockurl', tenant=None,
            passwd='passwd')
        self.assertIsNone(token.token)
        self.assertIsNone(token.tenant)
        self.assertIsNotNone(token.expires)

        m.post('http://mockurl/tokens', status_code=404)
        token = AdminToken(url='http://mockurl', tenant='tenant-id',
            passwd='passwd')

    @requests_mock.mock()
    def test_user_token(self, m):
        m.post('http://mockurl/tokens', text='\
            {"access": {"token": {"id": "the-token", \
            "expires": "2025-09-04T14:09:20.236Z"}}}')
        admintoken = AdminToken(url='http://mockurl', tenant='tenant-id',
            passwd='passwd')

        m.get('http://mockurl/tenants/tenant-id/users', status_code=404)
        usertoken = UserToken(url='http://mockurl', tenant='tenant-id',
            admintoken=admintoken)

        m.get('http://mockurl/tenants/tenant-id/users', text='\
            {"users": [{"id": "the-user-id"}]}')
        usertoken = UserToken(url='http://mockurl',
            tenant='tenant-id',
            admintoken=admintoken)

        m.get('http://mockurl/users/the-user-id/RAX-AUTH/admins',
            status_code=404)
        usertoken = UserToken(url='http://mockurl',
            tenant='tenant-id',
            admintoken=admintoken, token=None)
