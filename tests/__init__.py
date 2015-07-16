import uuid
import random
import unittest
from falcon import testing as ftest
from stealth.transport.wsgi import Driver, v1_0
import stealth.util.log as logging
import falcon


class DummyContextObject(object):
    pass


class TestBase(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super(TestBase, self).__init__(*args, **kwargs)

    def setUp(self):
        super(TestBase, self).setUp()
        import stealth
        stealth.context = DummyContextObject()
        stealth.context.project_id = self.create_project_id()
        stealth.context.openstack = DummyContextObject()
        stealth.context.openstack.auth_token = self.create_auth_token()
        stealth.context.openstack.swift = DummyContextObject()
        stealth.context.openstack.swift.storage_url = 'storage.url'
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
