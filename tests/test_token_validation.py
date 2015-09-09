from unittest import TestCase
from stealth.impl_rax.auth_token import AdminToken
from stealth.impl_rax.token_validation import get_auth_redis_client, \
    validate_client_token, validate_client_impersonation
from stealth import conf
import mock
# Mock requests
import requests
import requests_mock
import dateutil.parser
# Mock redis
import fakeredis
import redis
import simplejson as json


redis = fakeredis


def side_effect_exception(*args):
    raise Exception('mock exception')


def side_effect_redis_getdata(*args):
    return '{"token": "the-token", "tenant": "tenant-id", \
        "expires": "2025-09-04T14:09:20.236Z"}'


def side_effect_redis_getdata_expired(*args):
    return '{"token": "the-token", "tenant": "tenant-id", \
        "expires": "1025-09-04T14:09:20.236Z"}'


class TestAuthTokenCache(TestCase):

    def test_get_auth_redis_client(self):
        origval = conf.auth_redis.ssl_enable
        conf.auth_redis.ssl_enable = 'None'
        test_redis = get_auth_redis_client()
        conf.auth_redis.ssl_enable = 'True'
        test_redis = get_auth_redis_client()
        conf.auth_redis.ssl_enable = origval

    def test_validate_client_token(self):
        test_redis = get_auth_redis_client()
        self.assertIsNotNone(test_redis)
        retval, token = validate_client_token(
            test_redis, url='http://mockurl',
            tenant='tenant-id', cache_key='cache-key')
        self.assertFalse(retval)
        self.assertIsNone(token)

        with mock.patch.object(test_redis, 'get',
                side_effect=side_effect_redis_getdata):
            retval, token = validate_client_token(
                test_redis,
                url='http://mockurl',
                tenant='tenant-id',
                cache_key='cache-key')
            self.assertTrue(retval)
            self.assertEqual(token, 'the-token')

        with mock.patch.object(test_redis, 'get',
                side_effect=side_effect_redis_getdata_expired):
            retval, token = validate_client_token(
                test_redis,
                url='http://mockurl',
                tenant='tenant-id',
                cache_key='cache-key')
            self.assertFalse(retval)
            self.assertIsNone(token)

        with mock.patch.object(test_redis, 'get',
                side_effect=side_effect_exception):
            retval, token = validate_client_token(
                test_redis, url='http://mockurl',
                tenant='tenant-id', cache_key='cache-key')
            self.assertFalse(retval)
            self.assertIsNone(token)

        with mock.patch.object(test_redis, 'get',
                side_effect=side_effect_redis_getdata):
            with mock.patch.object(dateutil.parser, 'parse',
                    side_effect=side_effect_exception):
                retval, token = validate_client_token(test_redis,
                    url='http://mockurl',
                    tenant='tenant-id',
                    cache_key='cache-key')
            self.assertFalse(retval)
            self.assertIsNone(token)

    @requests_mock.mock()
    def test_validate_client_impersonation(self, m):
        test_redis = get_auth_redis_client()

        m.post('http://mockurl/tokens', text='\
            {"access": {"token": {"id": "the-token", \
            "expires": "2025-09-04T14:09:20.236Z"}}}')
        token_data = AdminToken(url='http://mockurl', tenant='tenant-id',
            passwd='passwd', token='thetoken')
        self.assertIsNone(token_data.token_data)

        m.get('http://mockurl/tenants/tenant-id/users', text='\
            {"users": [{"id": "the-user-id"}]}')
        m.get('http://mockurl/users/the-user-id/RAX-AUTH/admins', text='\
            {"users": [{"username": "the-user-name"}]}')
        m.post('http://mockurl/RAX-AUTH/impersonation-tokens', text='\
            {"access": {"token": {"id": "the-token",\
             "expires": "2025-09-04T14:09:20.236Z"}}}')
        retval, token, cache_key = validate_client_impersonation(test_redis,
            url='http://mockurl', tenant='tenant-id', admintoken=token_data)
        self.assertTrue(retval)
        self.assertIsNotNone(cache_key)
        self.assertEqual(token["expires"], "2025-09-04T14:09:20.236Z")
        self.assertEqual(token["tenant"], "tenant-id")
        self.assertEqual(token["token"], "the-token")

        m.post('http://mockurl/RAX-AUTH/impersonation-tokens', status_code=404)
        retval, token, cache_key = validate_client_impersonation(test_redis,
            url='http://mockurl', tenant='tenant-id', admintoken=token_data)
        self.assertFalse(retval)
        self.assertIsNone(token)
        self.assertIsNone(cache_key)
