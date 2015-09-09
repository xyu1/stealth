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

import uuid
import random
import unittest
from falcon import testing as ftest
import stealth.util.log as logging
import falcon
import requests_mock
import stealth
from stealth import conf


class DummyContextObject(object):
    pass


class TestBase(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super(TestBase, self).__init__(*args, **kwargs)

    @requests_mock.mock()
    def setUp(self, m):
        super(TestBase, self).setUp()
        m.post('http://mockurl/tokens', text='\
            {"access": {"token": {"id": "the-token", \
            "expires": "2025-09-04T14:09:20.236Z"}}}')
        m.get('http://mockurl/tenants/tenant-id/users', text='\
            {"users": [{"id": "the-user-id"}]}')
        m.get('http://mockurl/users/the-user-id/RAX-AUTH/admins', text='\
            {"users": [{"username": "the-user-name"}]}')
        m.post('http://mockurl/RAX-AUTH/impersonation-tokens', text='\
            {"access": {"token": {"id": "the-token",\
             "expires": "2025-09-04T14:09:20.236Z"}}}')
        conf.auth.auth_url = 'http://mockurl'
        stealth.context = DummyContextObject()
        stealth.context.project_id = self.create_project_id()
        stealth.context.openstack = DummyContextObject()
        stealth.context.openstack.auth_token = self.create_auth_token()
        stealth.context.openstack.swift = DummyContextObject()
        stealth.context.openstack.swift.storage_url = 'storage.url'

        from stealth.transport.wsgi import Driver, v1_0
        self._driver = Driver()
        self.app = self._driver.app

        self.srmock = ftest.StartResponseMock()
        self.headers = {}
        logging.setup()

    def tearDown(self):
        super(TestBase, self).tearDown()

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

    def create_auth_token(self):
        """Create a dummy Auth Token."""
        return 'auth_{0:}'.format(str(uuid.uuid4()))

    def create_project_id(self):
        """Create a dummy project ID. This needs to be
        6-7 digits long"""
        return str(random.randrange(100000, 9999999))

    def create_vault_id(self):
        """Creates a dummy vault ID. This could be
        anything, but for ease-of-use we just make it
        a uuid"""
        return 'vault_{0:}'.format(str(uuid.uuid4()))


class V1Base(TestBase):

    """Base class for V1 API Tests.

    Should contain methods specific to V1 of the API
    """
    pass
