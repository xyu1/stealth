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
from stealth.impl_rax.auth_token import TokenBase, AdminToken
from stealth.impl_rax.auth_token_cache import \
    _send_data_to_cache, _retrieve_data_from_cache
from stealth.impl_rax.token_validation import get_auth_redis_client
from stealth import conf
import mock
# Mock requests
import requests
import requests_mock
# Mock redis
import fakeredis
import redis


redis = fakeredis


def side_effect_exception(*args):
    raise Exception('mock exception')


def side_effect_redis_getdata(*args):
    return '{"token": "the-token", "tenant": "tenant-id", \
        "expires": "2125-09-04T14:09:20.236Z"}'


def side_effect_redis_getdata_wrong(*args):
    return '{"token": "the-token"}, "tenant": "tenant-id", \
        "expires": "2125-09-04T14:09:20.236Z"}'


def side_effect_redis_getdata_expired(*args):
    return '{"token": "the-token", "tenant": "tenant-id", \
        "expires": "1025-09-04T14:09:20.236Z"}'


class TestAuthTokenCache(TestCase):

    def test_token_cache(self):
        # get_auth_redis_client()
        origval = conf.auth_redis.ssl_enable
        conf.auth_redis.ssl_enable = 'None'
        test_redis = get_auth_redis_client()
        self.assertIsNotNone(test_redis)
        conf.auth_redis.ssl_enable = 'True'
        test_redis = get_auth_redis_client()
        self.assertIsNotNone(test_redis)
        conf.auth_redis.ssl_enable = origval

    @requests_mock.mock()
    def test_send_data_to_cache(self, m):
        test_redis = get_auth_redis_client()
        m.post('http://mockurl/tokens', text='{"access": \
            {"token": {"id": "the-token", "expires": \
            "2125-09-04T14:09:20.236Z"}}}')
        token_data = AdminToken(url='http://mockurl', tenant='\
            tenant-id', passwd='passwd', token='thetoken')
        self.assertIsNotNone(token_data)
        self.assertIsNone(token_data.token_data)
        # _send_data_to_cache()
        retval, key = _send_data_to_cache(test_redis, '', token_data)
        self.assertTrue(retval)
        self.assertIsNotNone(key)
        self.assertIsInstance(key, str)

        with mock.patch.object(test_redis, 'set',
                side_effect=side_effect_exception):
            retval, key = _send_data_to_cache(test_redis, '', token_data)
            self.assertFalse(retval)
            self.assertIsNone(key)

    def test_retrieve_data_from_cache(self):
        test_redis = get_auth_redis_client()
        self.assertIsNone(_retrieve_data_from_cache(test_redis,
            url='http://mockurl', tenant='tenant-id', cache_key=None))
        retval = _retrieve_data_from_cache(test_redis, url='http://mockurl',
            tenant='tenant-id', cache_key='cache-key')
        self.assertIsNone(retval)

        with mock.patch.object(test_redis, 'get',
                side_effect=side_effect_exception):
            self.assertIsNone(_retrieve_data_from_cache(test_redis,
                url='http://mockurl', tenant='tenant-id',
                cache_key='cache-key'))
        with mock.patch.object(test_redis, 'get',
                side_effect=side_effect_redis_getdata):
            retval = _retrieve_data_from_cache(test_redis,
                url='http://mockurl',
                tenant='tenant-id', cache_key='cache-key')
            self.assertIsNotNone(retval)
            self.assertEqual(retval['tenant'], 'tenant-id')
            self.assertEqual(retval['token'], 'the-token')
            self.assertEqual(retval['expires'], '2125-09-04T14:09:20.236Z')
        with mock.patch.object(test_redis, 'get',
                side_effect=side_effect_redis_getdata_wrong):
            self.assertIsNone(_retrieve_data_from_cache(test_redis,
                url='http://mockurl', tenant='tenant-id',
                cache_key='cache-key'))
