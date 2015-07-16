from hashlib import md5
from random import randrange
from unittest import TestCase
from stealth.util import set_qs, set_qs_on_url, relative_uri

try:  # pragma: no cover
    import six.moves.urllib.parse as parse
except ImportError:  # pragma: no cover
    import urllib.parse as parse

# TODO: We probably want to move this to a
# test helpers library


class TestUtil(TestCase):

    def test_set_qs_on_url(self):
        url = 'http://whatever:8080/hello/world'

        # Empty case
        query_string = set_qs(url, args={'param1': 'value1'})
        self.assertEqual('param1=value1', query_string)

    def test_set_qs(self):
        url = 'http://whatever:8080/hello/world?param1=value1&param2=value2'

        # Empty case
        testurl = set_qs_on_url(url)
        self.assertEqual(testurl, 'http://whatever:8080/hello/world')

        uri, querystring = relative_uri(testurl)

        positive_cases = [
            {'whatever': '3'},
            {'hello': 'whatever'},
            {'yes': u'whatever'}
        ]

        for args in positive_cases:
            output = set_qs(url, args)
            parts = parse.urlparse(output)

            qs = parts.query
            output = parse.parse_qs(qs)
