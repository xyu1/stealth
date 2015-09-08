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
        self.assertIsNone(token.token_data)

    @requests_mock.mock()
    def test_user_token(self, m):
        m.post('http://mockurl.com/tokens', status_code=404)
        admintoken = AdminToken(url='http://mockurl.com', tenant='tenant-id',
            passwd='passwd')
        self.assertIsNone(admintoken.token_data)

        m.post('http://mockurl.com/tokens', text='\
            {"access": {"token": {"id": "the-token", \
            "expires": "2125-09-04T14:09:20.236Z"}}}')
        admintoken = AdminToken(url='http://mockurl.com', tenant='tenant-id',
            passwd='passwd')
        self.assertIsNotNone(admintoken.token_data)
        self.assertEqual(admintoken.token_data['tenant'], 'tenant-id')
        self.assertEqual(admintoken.token_data['token'], 'the-token')
        self.assertEqual(admintoken.token_data['expires'],
            '2125-09-04T14:09:20.236Z')

        m.get('http://mockurl.com/tenants/tenant-id/users', status_code=404)
        usertoken = UserToken(url='http://mockurl.com', tenant='tenant-id',
            admintoken=admintoken)
        self.assertIsNone(usertoken.token_data)

        m.get('http://mockurl.com/tenants/tenant-id/users', text='\
            {"users": [{"id": "the-user-id"}]}')
        usertoken = UserToken(url='http://mockurl.com',
            tenant='tenant-id',
            admintoken=admintoken)
        self.assertIsNone(usertoken.token_data)

        m.get('http://mockurl.com/users/the-user-id/RAX-AUTH/admins',
            status_code=404)
        usertoken = UserToken(url='http://mockurl.com',
            tenant='tenant-id',
            admintoken=admintoken, token=None)
        self.assertIsNone(usertoken.token_data)
