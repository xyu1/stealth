import msgpack
import functools
import random
from unittest import TestCase
import fakeredis
import falcon
from stealth.util import auth_app
import mock
from stealth.util import auth_endpoint
import httpretty
import datetime
from oslo_utils import timeutils


# Monkey patch the FakeRedis so we can expire data - even if it does nothing
def fakeredis_pexpireat(self, key, when):
    pass
fakeredis.FakeRedis.pexpireat = fakeredis_pexpireat


def fakeredis_pexpire(self, key, ttl):
    pass
fakeredis.FakeRedis.pexpire = fakeredis_pexpire


def fakeredis_connection():
    return fakeredis.FakeRedis()


def _tuple_to_cache_key(t):
    """Convert a tuple to a cache key."""
    key = ''
    if t and len(t) > 0:
        key = '(%(s_data)s)' % {
            's_data': ','.join(t)
        }
    return key

__unpacker = functools.partial(msgpack.unpackb, encoding='utf-8')


# NOTE: from __init__.py testbase
def create_project_id():
    return str(random.randrange(100000, 9999999))


class Response(object):
    def __init__(self):
        self._status = None
        self._headers = None

    def start_response(self, status, headers=None):
        self._status = status
        self._headers = headers

    @property
    def status(self):
        return self._status

    @property
    def headers(self):
        return self._headers


class TestAuthApp(TestCase):

    def setUp(self):
        super(TestAuthApp, self).setUp()

    def tearDown(self):
        super(TestAuthApp, self).tearDown()

    @httpretty.activate
    def test_auth_get(self):
        self.resp = Response()
        self.redis_client = fakeredis_connection()
        self.projid = create_project_id()
        self.auth_url = 'http://sample.com'
        self.auth = auth_app.app(self.redis_client, auth_url=self.auth_url)

        url = self.auth_url + '/tenants/' + self.projid + '/users'
        body = '{"users": [{"id": "mocking_id"}]}'
        httpretty.register_uri(httpretty.GET,
            url,
            status=200,
            body=body)

        url = self.auth_url + '/users/mocking_id/RAX-AUTH/admins'
        body = '{"users": [{"username": "mocking_name"}]}'
        httpretty.register_uri(httpretty.GET,
            url,
            status=200,
            body=body)

        url = self.auth_url + '/RAX-AUTH/impersonation-tokens'
        body = '{"access":{"token": {"id": "' + self.projid + \
            '", "expires": "' + \
            str(timeutils.utcnow() + datetime.timedelta(seconds=30)) + \
            '"}}}'
        httpretty.register_uri(httpretty.POST,
            url,
            status=200,
            body=body)

        env = {}
        env['HTTP_X_PROJECT_ID'] = self.projid
        self.auth(env, self.resp.start_response)

        self.assertEqual(self.resp.status, falcon.HTTP_204)
        self.assertEqual(self.resp.headers,
          [("X-AUTH-TOKEN", str(self.projid))])

    @httpretty.activate
    def test_auth_failure(self):
        self.resp = Response()
        self.redis_client = fakeredis_connection()
        self.projid = create_project_id()
        self.auth_url = 'http://sample.com'
        env = {}

        ##
        self.auth = auth_app.app(self.redis_client, auth_url=None)

        ##
        admin_name = 'notmatter'
        admin_pass = 'notmatter'
        url = self.auth_url + '/tokens'
        body = '{"access":{"token": {"id": "mocking", "expires": "' + \
            str(timeutils.utcnow() + datetime.timedelta(seconds=30)) + \
            '"}}}'
        httpretty.register_uri(httpretty.POST,
            url,
            status=200,
            body=body)
        self.auth = auth_app.app(self.redis_client,
          auth_url=self.auth_url, admin_name=admin_name, admin_pass=admin_pass)

        ##
        self.auth = auth_app.app(self.redis_client, auth_url=self.auth_url)
        self.auth(env, self.resp.start_response)
        self.assertEqual(self.resp.status, falcon.HTTP_412)

        url = self.auth_url + '/tenants/' + self.projid + '/users'
        body = ''
        httpretty.register_uri(httpretty.GET,
            url,
            status=401,
            body=body)

        env['HTTP_X_PROJECT_ID'] = self.projid
        self.auth(env, self.resp.start_response)

        env['HTTP_X_AUTH_TOKEN'] = 'mocking'
        self.auth(env, self.resp.start_response)

        ##
        cache_data = msgpack.Packer(encoding='utf-8',
            use_bin_type=True).pack('{"token": "mocking", "tenant": ' +
            str(self.projid) + ', "expires": "' +
            str(timeutils.utcnow() + datetime.timedelta(seconds=3000)) +
            '"}')
        cache_key = _tuple_to_cache_key((self.projid, self.auth_url))
        self.redis_client.set(cache_key, cache_data)
        self.auth(env, self.resp.start_response)


class Requests(object):
    def __init__(self, headers):
        self._headers = headers

    @property
    def headers(self):
        return self._headers


class Responses(object):
    def __init__(self):
        self._headers = dict()

    def set_header(self, name, value):
        self._headers[name] = value


class TestAuthEndpoint(TestCase):

    def setUp(self):
        super(TestAuthEndpoint, self).setUp()

    def tearDown(self):
        super(TestAuthEndpoint, self).tearDown()

    @httpretty.activate
    def test_auth_endpoint_get(self):
        self.redis_client = fakeredis_connection()
        self.projid = create_project_id()
        self.auth_url = 'http://sample.com'
        headers = dict({'X-AUTH-TOKEN': 'mockingtoken'})
        self.req = Requests(headers)
        self.resp = Responses()

        admin_name = 'notmatter'
        admin_pass = 'notmatter'
        url = self.auth_url + '/tokens'
        body = '{"access":{"token": {"id": "mocking", "expires": "' + \
            str(timeutils.utcnow() + datetime.timedelta(seconds=30)) + \
            '"}}}'
        httpretty.register_uri(httpretty.POST,
            url,
            status=200,
            body=body)

        url = self.auth_url + '/tenants/' + self.projid + '/users'
        body = '{"users": [{"id": "mocking_id"}]}'
        httpretty.register_uri(httpretty.GET,
            url,
            status=200,
            body=body)

        url = self.auth_url + '/users/mocking_id/RAX-AUTH/admins'
        body = '{"users": [{"username": "mocking_name"}]}'
        httpretty.register_uri(httpretty.GET,
            url,
            status=200,
            body=body)

        url = self.auth_url + '/RAX-AUTH/impersonation-tokens'
        body = '{"access":{"token": {"id": "' + self.projid + \
            '", "expires": "' + \
            str(timeutils.utcnow() + datetime.timedelta(seconds=30)) + \
            '"}}}'
        httpretty.register_uri(httpretty.POST,
            url,
            status=200,
            body=body)
        self.authserv = auth_endpoint.AuthServ(self.redis_client,
          auth_url=self.auth_url)

        succ, msg = self.authserv.auth(self.req, self.resp, self.projid)
        print(succ, msg)

        # self.assertIn('X-AUTH-TOKEN', self.auth)

        # print (self.resp._headers)
    '''
        env = {}
        env['HTTP_X_PROJECT_ID'] = self.projid
        self.auth(env, self.resp.start_response)

        self.assertEqual(self.resp.status, falcon.HTTP_204)
        self.assertEqual(self.resp.headers,
          [("X-AUTH-TOKEN", str(self.projid))])

    '''

    '''
    @httpretty.activate
    def test_auth_endpoint_failure(self):
        self.redis_client = fakeredis_connection()
        self.projid = create_project_id()
        self.auth_url = 'http://sample.com'
        env = {}

        ##
        self.auth = auth_app.app(self.redis_client, auth_url=None)

        ##
        admin_name = 'notmatter'
        admin_pass = 'notmatter'
        url = self.auth_url + '/tokens'
        body = '{"access":{"token": {"id": "mocking", "expires": "' + \
            str(timeutils.utcnow() + datetime.timedelta(seconds=30)) + \
            '"}}}'
        httpretty.register_uri(httpretty.POST,
            url,
            status=200,
            body=body)
        self.auth = auth_app.app(self.redis_client,
          auth_url=self.auth_url, admin_name=admin_name, admin_pass=admin_pass)

        ##
        self.auth = auth_app.app(self.redis_client, auth_url=self.auth_url)
        self.auth(env, self.resp.start_response)
        self.assertEqual(self.resp.status, falcon.HTTP_412)

        url = self.auth_url + '/tenants/' + self.projid + '/users'
        body = ''
        httpretty.register_uri(httpretty.GET,
            url,
            status=401,
            body=body)

        env['HTTP_X_PROJECT_ID'] = self.projid
        self.auth(env, self.resp.start_response)

        env['HTTP_X_AUTH_TOKEN'] = 'mocking'
        self.auth(env, self.resp.start_response)

        ##
        cache_data = msgpack.Packer(encoding='utf-8',
            use_bin_type=True).pack('{"token": \
            "mocking", "tenant": '+str(self.projid) + ', "expires": "' + \
            str(timeutils.utcnow() + datetime.timedelta(seconds=3000)) + \
            '"}')
        cache_key = _tuple_to_cache_key((self.projid, self.auth_url))
        self.redis_client.set(cache_key, cache_data)
        self.auth(env, self.resp.start_response)
    '''
