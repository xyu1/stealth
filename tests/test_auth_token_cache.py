from unittest import TestCase
from stealth.impl_rax.auth_token import TokenBase, AdminToken
from stealth.impl_rax.auth_token_cache import \
    _send_data_to_cache, _retrieve_data_from_cache
from stealth.impl_rax.token_validation import get_auth_redis_client
from stealth import conf
import mock
# Mock requests
import requests
import requests_mock
import dateutil.parser
# Mock redis
import fakeredis
import redis


redis = fakeredis


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


class TestAuthTokenCache(TestCase):

    def test_token_cache(self):
        # get_auth_redis_client()
        origval = conf.auth_redis.ssl_enable
        conf.auth_redis.ssl_enable = 'None'
        test_redis = get_auth_redis_client()
        conf.auth_redis.ssl_enable = 'True'
        test_redis = get_auth_redis_client()
        conf.auth_redis.ssl_enable = origval

    @requests_mock.mock()
    def test_send_data_to_cache(self, m):
        test_redis = get_auth_redis_client()
        m.post('http://mockurl/tokens', text='{"access": \
            {"token": {"id": "the-token", "expires": \
            "2025-09-04T14:09:20.236Z"}}}')
        token_data = AdminToken(url='http://mockurl', tenant='\
            tenant-id', passwd='passwd', token='thetoken')
        # _send_data_to_cache()
        _send_data_to_cache(test_redis, '', token_data)

        with mock.patch.object(test_redis, 'set',
                side_effect=side_effect_exception):
            _send_data_to_cache(test_redis, '', token_data)

    def test_retrieve_data_from_cache(self):
        test_redis = get_auth_redis_client()
        self.assertIsNone(_retrieve_data_from_cache(test_redis,
            url='http://mockurl', tenant='tenant-id', cache_key=None))
        _retrieve_data_from_cache(test_redis, url='http://mockurl',
            tenant='tenant-id', cache_key='cache-key')
        with mock.patch.object(test_redis, 'get',
                side_effect=side_effect_exception):
            self.assertIsNone(_retrieve_data_from_cache(test_redis,
                url='http://mockurl', tenant='tenant-id',
                cache_key='cache-key'))
        with mock.patch.object(test_redis, 'get',
                side_effect=side_effect_redis_getdata):
            _retrieve_data_from_cache(test_redis, url='http://mockurl',
                tenant='tenant-id', cache_key='cache-key')
        with mock.patch.object(test_redis, 'get',
                side_effect=side_effect_redis_getdata_wrong):
            self.assertIsNone(_retrieve_data_from_cache(test_redis,
                url='http://mockurl', tenant='tenant-id',
                cache_key='cache-key'))
