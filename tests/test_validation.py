import hashlib
from unittest import TestCase
import uuid

from falcon import request
from stoplight import validate
from stoplight.exceptions import ValidationFailed

from stealth.transport import validation as v
from stealth.transport.wsgi import errors


class MockRequest(object):
    pass


class InvalidSeparatorError(Exception):
    """Invalid Separator Error is raised whenever
    a invalid separator is set for joining query strings
    in a url"""

    def __init__(self, msg):
        Exception.__init__(self, msg)


class TestRulesBase(TestCase):

    @staticmethod
    def build_request(params=None, separator='&'):
        """Build a request object to use for testing

        :param params: list of tuples containing the name and value pairs
                       for parameters to add to the QUERY_STRING
        """
        mock_env = {
            'wsgi.errors': 'mock',
            'wsgi.input': 'mock',
            'REQUEST_METHOD': 'PUT',
            'PATH_INFO': '/',
            'SERVER_NAME': 'mock',
            'SERVER_PORT': '8888',
            'QUERY_STRING': None
        }

        if params is not None:
            for param in params:
                name = param[0]
                value = param[1]

                param_set = '{0}='.format(name)
                if value is not None and len(value):
                    param_set = '{0}={1}'.format(name, value)

                if mock_env['QUERY_STRING'] is None:
                    mock_env['QUERY_STRING'] = param_set
                else:
                    if separator in ('&', ';'):
                        mock_env['QUERY_STRING'] = '{1}{0}{2}'.format(
                            separator, mock_env['QUERY_STRING'], param_set)
                    else:
                        raise InvalidSeparatorError('separator in query string'
                                                    'must be & or ;')

        if mock_env['QUERY_STRING'] is None:
            del mock_env['QUERY_STRING']

        return request.Request(mock_env)

    def cases_with_none_okay(self):

        positive_cases = self.__class__.positive_cases[:]
        positive_cases.append(None)

        negative_cases = self.__class__.negative_cases[:]
        while negative_cases.count(None):
            negative_cases.remove(None)
        while negative_cases.count(''):
            negative_cases.remove('')

        return (positive_cases, negative_cases)


class TestRequests(TestRulesBase):

    def test_request(self):

        positive_case = [TestRulesBase.build_request()]

        negative_case = [MockRequest()]

        for case in positive_case:
            v.is_request(case)

        for case in negative_case:
            with self.assertRaises(ValidationFailed):
                v.is_request(none_ok=True)(case)


class TestProjectIDRules(TestRulesBase):

    positive_cases = [
        '100000', '9999999'
    ]

    negative_cases = [
        '-1', 'blah', None
    ]

    @validate(req=v.RequestRule(v.ProjectIDRule))
    def utilize_request(self, req, raiseme=False):
        if raiseme:
            raise RuntimeError('QUERY_STRING: {0}'.format(req.query_string))
        else:
            return True

    def test_projectid(self):

        for projectid in self.__class__.positive_cases:
            v.val_projectid()(projectid)

        for projectid in self.__class__.negative_cases:
            with self.assertRaises(ValidationFailed):
                v.val_projectid()(projectid)

        v.val_projectid(empty_ok=True)('')
        v.val_projectid(none_ok=True)(None)

        with self.assertRaises(ValidationFailed):
            v.val_projectid()('')

        with self.assertRaises(ValidationFailed):
            v.val_projectid()(None)
