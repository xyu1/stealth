from unittest import TestCase
from stealth.impl_rax.auth_token import AdminToken, UserToken
# Mock requests
import requests
import requests_mock


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
        m.post('http://mockurl.com/tokens', status_code=404)
        admintoken = AdminToken(url='http://mockurl.com', tenant='tenant-id',
            passwd='passwd')

        m.post('http://mockurl.com/tokens', text='\
            {"access": {"token": {"id": "the-token", \
            "expires": "2025-09-04T14:09:20.236Z"}}}')
        admintoken = AdminToken(url='http://mockurl.com', tenant='tenant-id',
            passwd='passwd')

        m.get('http://mockurl.com/tenants/tenant-id/users', status_code=404)
        usertoken = UserToken(url='http://mockurl.com', tenant='tenant-id',
            admintoken=admintoken)

        m.get('http://mockurl.com/tenants/tenant-id/users', text='\
            {"users": [{"id": "the-user-id"}]}')
        usertoken = UserToken(url='http://mockurl.com',
            tenant='tenant-id',
            admintoken=admintoken)

        m.get('http://mockurl.com/users/the-user-id/RAX-AUTH/admins',
            status_code=404)
        usertoken = UserToken(url='http://mockurl.com',
            tenant='tenant-id',
            admintoken=admintoken, token=None)
