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


class TestVaultRules(TestRulesBase):

    positive_cases = [
        'a',
        '0',
        '__vault_id____',
        '-_-_-_-_-_-_-_-',
        'snake_case_is_ok',
        'So-are-hyphonated-names',
        'a' * v.VAULT_ID_MAX_LEN
    ]

    negative_cases = [
        '',  # empty case should raise
        '.', '!', '@', '#', '$', '%',
        '^', '&', '*', '[', ']', '/',
        '@#$@#$@#^@%$@#@#@#$@!!!@$@$@',
        '\\', 'a' * (v.VAULT_ID_MAX_LEN + 1),
        None
    ]

    @validate(vault_id=v.VaultGetRule)
    def utilize_get_vault_id(self, vault_id):
        return True

    @validate(vault_id=v.VaultPutRule)
    def utilize_put_vault_id(self, vault_id):
        return True

    def utilize_request(self, req, raiseme=False):
        if raiseme:
            raise RuntimeError('QUERY_STRING: {0}'.format(req.query_string))
        else:
            return True

    def test_vault_id(self):

        for name in self.__class__.positive_cases:
            v.val_vault_id(name)

        for name in self.__class__.negative_cases:
            with self.assertRaises(ValidationFailed):
                v.val_vault_id()(name)

    def test_vault_get(self):

        for p_case in self.__class__.positive_cases:
            self.assertTrue(self.utilize_get_vault_id(p_case))

        for case in self.__class__.negative_cases:
            with self.assertRaises(errors.HTTPNotFound):
                self.utilize_get_vault_id(case)

    def test_vault_put(self):

        for p_case in self.__class__.positive_cases:
            self.assertTrue(self.utilize_put_vault_id(p_case))

        for case in self.__class__.negative_cases:
            with self.assertRaises(errors.HTTPBadRequestAPI):
                self.utilize_put_vault_id(case)

    def test_vault_id_marker(self):

        positive_cases, negative_cases = self.cases_with_none_okay()

        for vault_id in positive_cases:
            vault_id_req = TestRulesBase.build_request(params=[('marker',
                                                                vault_id)])
            self.assertTrue(self.utilize_request(vault_id_req))

        # We currently skip the negative test for the VaultMarkerRule
        # due to the nature of the negative cases for the Vault Name.
        # Leaving the code in below should we figure out a good way to
        # capture the data for the URL encoding.
        #
        # Note: It is not a failure of build_request()'s QUERY_STRING building
        #   but a miss-match between it, urllib.parse.urlencode(), and Falcon.
        #   Use of urllib.parse.urlencode() has other issues here as well.
        #
        # for vault_id in negative_cases:
        #    vault_id_req = TestRulesBase.build_request(params=[('marker',
        #                                                        vault_id)])
        #    with self.assertRaises(errors.HTTPNotFound):
        #        self.utilize_request(vault_id_req, raiseme=True)


class TestMetadataBlockRules(TestRulesBase):

    positive_cases = [
        'da39a3ee5e6b4b0d3255bfef95601890afd80709',
        'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa',
        'ffffffffffffffffffffffffffffffffffffffff',
        'a' * 40,
    ]

    negative_cases = [
        '',
        '.',
        'a', '0', 'f', 'F', 'z', '#', '$', '?',
        'a39a3ee5e6b4b0d3255bfef95601890afd80709',  # one char short
        'da39a3ee5e6b4b0d3255bfef95601890afd80709a',  # one char long
        'DA39A3EE5E6B4B0D3255BFEF95601890AFD80709',
        'FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF',
        'AaaAaaAaaaaAaAaaaAaaaaaaaAAAAaaaaAaaaaaa' * 2,
        'AaaAaaAaaaaAaAaaaAaaaaaaaAAAAaaaaAaaaaaa' * 3,
        'AaaAaaAaaaaAaAaaaAaaaaaaaAAAAaaaaAaaaaaa' * 4,
        None
    ]

    @validate(metadata_block_id=v.BlockGetRule)
    def utilize_get_metadata_block_get(self, metadata_block_id):
        return True

    @validate(metadata_block_id=v.BlockPutRule)
    def utilize_put_metadata_block_id(self, metadata_block_id):
        return True

    @validate(metadata_block_id=v.BlockPostRule)
    def utilize_post_metadata_block_id(self, metadata_block_id):
        return True

    @validate(metadata_block_id=v.BlockGetRuleNoneOk)
    def utilize_get_metadata_block_get_none_okay(self, metadata_block_id):
        return True

    @validate(metadata_block_id=v.BlockPutRuleNoneOk)
    def utilize_put_metadata_block_id_none_okay(self, metadata_block_id):
        return True

    @validate(metadata_block_id=v.BlockPostRuleNoneOk)
    def utilize_post_metadata_block_id_none_okay(self, metadata_block_id):
        return True

    @validate(req=v.RequestRule(v.BlockMarkerRule))
    def utilize_request(self, req, raiseme=False):
        if raiseme:
            raise RuntimeError('QUERY_STRING: {0}'.format(req.query_string))
        else:
            return True

    def test_block_id(self):

        for blockid in self.__class__.positive_cases:
            v.val_block_id(blockid)

        for blockid in self.__class__.negative_cases:
            with self.assertRaises(v.ValidationFailed):
                v.val_block_id()(blockid)

    def test_get_block_id(self):

        for blockid in self.__class__.positive_cases:
            self.utilize_get_metadata_block_get(blockid)

        for blockid in self.__class__.negative_cases:
            with self.assertRaises(errors.HTTPNotFound):
                self.utilize_get_metadata_block_get(blockid)

    def test_put_block_id(self):

        for blockid in self.__class__.positive_cases:
            self.utilize_put_metadata_block_id(blockid)

        for blockid in self.__class__.negative_cases:
            with self.assertRaises(errors.HTTPBadRequestAPI):
                self.utilize_put_metadata_block_id(blockid)

    def test_get_block_id_none_okay(self):

        positive_cases, negative_cases = self.cases_with_none_okay()

        for blockid in positive_cases:
            self.utilize_get_metadata_block_get_none_okay(blockid)

        for blockid in negative_cases:
            with self.assertRaises(errors.HTTPNotFound):
                self.utilize_get_metadata_block_get_none_okay(blockid)

    def test_put_block_id_none_okay(self):

        positive_cases, negative_cases = self.cases_with_none_okay()

        for blockid in positive_cases:
            self.utilize_put_metadata_block_id_none_okay(blockid)

        for blockid in negative_cases:
            with self.assertRaises(errors.HTTPBadRequestAPI):
                self.utilize_put_metadata_block_id_none_okay(blockid)

    def test_post_block_id(self):

        for blockid in self.__class__.positive_cases:
            self.utilize_post_metadata_block_id(blockid)

        for blockid in self.__class__.negative_cases:
            with self.assertRaises(errors.HTTPBadRequestAPI):
                self.utilize_post_metadata_block_id(blockid)

    def test_post_block_id_none_okay(self):

        positive_cases, negative_cases = self.cases_with_none_okay()

        for blockid in positive_cases:
            self.utilize_post_metadata_block_id_none_okay(blockid)

        for blockid in negative_cases:
            with self.assertRaises(errors.HTTPBadRequestAPI):
                self.utilize_post_metadata_block_id_none_okay(blockid)

    def test_block_id_marker(self):

        positive_cases, negative_cases = self.cases_with_none_okay()

        for block_id in positive_cases:
            block_id_req = TestRulesBase.build_request(params=[('marker',
                                                                block_id)])
            self.assertTrue(self.utilize_request(block_id_req))

        for block_id in negative_cases:
            block_id_req = TestRulesBase.build_request(params=[('marker',
                                                                block_id)])

            with self.assertRaises(errors.HTTPNotFound):
                self.utilize_request(block_id_req, raiseme=True)


class TestStorageBlockRules(TestRulesBase):

    positive_cases = [hashlib.sha1(bytes(i)).hexdigest() + '_' +
                      str(uuid.uuid4()) for i in range(0, 1000)]

    negative_cases = [
        '',
        'fecfd28bbc9345891a66d7c1b8ff46e60192d'
        '2840c3de7c4-5fe9-4b2e-b19a-9cf81364997b',  # note no '_' between sha1
                                                    #  and uuid
        'e7bf692b-ec7b-40ad-b0d1-45ce6798fb6z',  # note trailing z
        str(uuid.uuid4()).upper(),  # Force case sensitivity
        None
    ]

    @validate(storage_block_id=v.StorageBlockGetRule)
    def utilize_get_storage_block_get(self, storage_block_id):
        return True

    @validate(storage_block_id=v.StorageBlockPutRule)
    def utilize_put_storage_block_id(self, storage_block_id):
        return True

    @validate(storage_block_id=v.StorageBlockRuleGetNoneOk)
    def utilize_get_storage_block_get_none_okay(self, storage_block_id):
        return True

    @validate(storage_block_id=v.StorageBlockRulePutNoneOk)
    def utilize_put_storage_block_id_none_okay(self, storage_block_id):
        return True

    @validate(req=v.RequestRule(v.StorageBlockMarkerRule))
    def utilize_request(self, req, raiseme=False):
        if raiseme:
            raise RuntimeError('QUERY_STRING: {0}'.format(req.query_string))
        else:
            return True

    def test_storage_storage_block_id(self):

        for storage_id in self.__class__.positive_cases:
            v.val_storage_block_id(storage_id)

        for storage_id in self.__class__.negative_cases:
            with self.assertRaises(ValidationFailed):
                v.val_storage_block_id()(storage_id)

    def test_get_storage_block_id(self):

        for storage_id in self.__class__.positive_cases:
            self.utilize_get_storage_block_get(storage_id)

        for storage_id in self.__class__.negative_cases:
            with self.assertRaises(errors.HTTPNotFound):
                self.utilize_get_storage_block_get(storage_id)

    def test_put_storage_block_id(self):

        for storage_id in self.__class__.positive_cases:
            self.utilize_put_storage_block_id(storage_id)

        for storage_id in self.__class__.negative_cases:
            with self.assertRaises(errors.HTTPBadRequestAPI):
                self.utilize_put_storage_block_id(storage_id)

    def test_get_storage_block_id_none_okay(self):

        positive_cases, negative_cases = self.cases_with_none_okay()

        for storage_id in positive_cases:
            self.utilize_get_storage_block_get_none_okay(storage_id)

        for storage_id in negative_cases:
            with self.assertRaises(errors.HTTPNotFound):
                self.utilize_get_storage_block_get_none_okay(storage_id)

    def test_put_storage_block_id_none_okay(self):

        positive_cases, negative_cases = self.cases_with_none_okay()

        for storage_id in positive_cases:
            self.utilize_put_storage_block_id_none_okay(storage_id)

        for storage_id in negative_cases:
            with self.assertRaises(errors.HTTPBadRequestAPI):
                self.utilize_put_storage_block_id_none_okay(storage_id)

    def test_storage_block_id_marker(self):

        positive_cases, negative_cases = self.cases_with_none_okay()

        for storage_id in positive_cases:
            storage_id_req = TestRulesBase.build_request(params=[('marker',
                                                                storage_id)])
            self.assertTrue(self.utilize_request(storage_id_req))

        for storage_id in negative_cases:
            storage_id_req = TestRulesBase.build_request(params=[('marker',
                                                                storage_id)])

            with self.assertRaises(errors.HTTPNotFound):
                self.utilize_request(storage_id_req, raiseme=True)


class TestFileRules(TestRulesBase):

    # Let's try try to append some UUIds and check for faileus
    positive_cases = [str(uuid.uuid4()) for _ in range(0, 1000)]

    negative_cases = [
        '',
        'e7bf692b-ec7b-40ad-b0d1-45ce6798fb6z',  # note trailing z
        str(uuid.uuid4()).upper(),  # Force case sensitivity
        None
    ]

    @validate(file_id=v.FileGetRule)
    def utilize_file_id_get(self, file_id):
        return True

    @validate(file_id=v.FilePutRule)
    def utilize_file_id_put(self, file_id):
        return True

    @validate(file_id=v.FilePostRule)
    def utilize_file_id_post(self, file_id):
        return True

    @validate(file_id=v.FileGetRuleNoneOk)
    def utilize_file_id_get_none_okay(self, file_id):
        return True

    @validate(file_id=v.FilePutRuleNoneOk)
    def utilize_file_id_put_none_okay(self, file_id):
        return True

    @validate(file_id=v.FilePostRuleNoneOk)
    def utilize_file_id_post_none_okay(self, file_id):
        return True

    @validate(req=v.RequestRule(v.FileMarkerRule))
    def utilize_request(self, req, raiseme=False):
        if raiseme:
            raise RuntimeError('QUERY_STRING: {0}'.format(req.query_string))
        else:
            return True

    def test_file_id(self):

        for fileid in self.__class__.positive_cases:
            v.val_file_id(fileid)

        for fileid in self.__class__.negative_cases:
            with self.assertRaises(ValidationFailed):
                v.val_file_id()(fileid)

    def test_get_file_id(self):

        for file_id in self.__class__.positive_cases:
            self.utilize_file_id_get(file_id)

        for file_id in self.__class__.negative_cases:
            with self.assertRaises(errors.HTTPNotFound):
                self.utilize_file_id_get(file_id)

    def test_put_file_id(self):

        for file_id in self.__class__.positive_cases:
            self.utilize_file_id_put(file_id)

        for file_id in self.__class__.negative_cases:
            with self.assertRaises(errors.HTTPBadRequestAPI):
                self.utilize_file_id_put(file_id)

    def test_post_file_id(self):

        for file_id in self.__class__.positive_cases:
            self.utilize_file_id_post(file_id)

        for file_id in self.__class__.negative_cases:
            with self.assertRaises(errors.HTTPBadRequestAPI):
                self.utilize_file_id_post(file_id)

    def test_get_file_id_none_okay(self):

        positive_cases, negative_cases = self.cases_with_none_okay()

        for file_id in positive_cases:
            self.utilize_file_id_get_none_okay(file_id)

        for file_id in negative_cases:
            with self.assertRaises(errors.HTTPNotFound):
                self.utilize_file_id_get_none_okay(file_id)

    def test_put_file_id_none_okay(self):

        positive_cases, negative_cases = self.cases_with_none_okay()

        for file_id in positive_cases:
            self.utilize_file_id_put_none_okay(file_id)

        for file_id in negative_cases:
            with self.assertRaises(errors.HTTPBadRequestAPI):
                self.utilize_file_id_put_none_okay(file_id)

    def test_post_file_id_none_okay(self):

        positive_cases, negative_cases = self.cases_with_none_okay()

        for file_id in positive_cases:
            self.utilize_file_id_post_none_okay(file_id)

        for file_id in negative_cases:
            with self.assertRaises(errors.HTTPBadRequestAPI):
                self.utilize_file_id_post_none_okay(file_id)

    def test_file_id_marker(self):

        positive_cases, negative_cases = self.cases_with_none_okay()

        for file_id in positive_cases:
            file_id_req = TestRulesBase.build_request(params=[('marker',
                                                               file_id)])
            self.assertTrue(self.utilize_request(file_id_req))

        for file_id in negative_cases:
            file_id_req = TestRulesBase.build_request(params=[('marker',
                                                               file_id)])

            with self.assertRaises(errors.HTTPNotFound):
                self.utilize_request(file_id_req, raiseme=True)


class TestOffsetRules(TestRulesBase):

    positive_cases = [
        '0', '1', '2', '3', '55', '100',
        '101010', '99999999999999999999999999999'
    ]

    negative_cases = [
        '-1', '-23', 'O', 'zero', 'one', '-999', '1.0', '1.3',
        '0.0000000000001',
        None
    ]

    @validate(req=v.RequestRule(v.OffsetMarkerRule))
    def utilize_request(self, req, raiseme=False):
        if raiseme:
            raise RuntimeError('QUERY_STRING: {0}'.format(req.query_string))
        else:
            return True

    def test_offset(self):

        for offset in self.__class__.positive_cases:
            v.val_offset()(offset)

        for offset in self.__class__.negative_cases:
            with self.assertRaises(ValidationFailed):
                v.val_offset()(offset)

    def test_offset_marker(self):

        positive_cases, negative_cases = self.cases_with_none_okay()

        for offset in positive_cases:
            offset_req = TestRulesBase.build_request(params=[('marker',
                                                              offset)])
            self.assertTrue(self.utilize_request(offset_req))

        for offset in negative_cases:
            offset_req = TestRulesBase.build_request(params=[('marker',
                                                              offset)])
            with self.assertRaises(errors.HTTPNotFound):
                self.utilize_request(offset_req, raiseme=True)


class TestLimitRules(TestRulesBase):

    positive_cases = [
        '0', '100', '100000000', '100'
    ]

    negative_cases = [
        '-1', 'blah', None
    ]

    @validate(req=v.RequestRule(v.LimitRule))
    def utilize_request(self, req, raiseme=False):
        if raiseme:
            raise RuntimeError('QUERY_STRING: {0}'.format(req.query_string))
        else:
            return True

    def test_limit(self):

        for limit in self.__class__.positive_cases:
            v.val_limit()(limit)

        for limit in self.__class__.negative_cases:
            with self.assertRaises(ValidationFailed):
                v.val_limit()(limit)

        v.val_limit(empty_ok=True)('')
        v.val_limit(none_ok=True)(None)

        with self.assertRaises(ValidationFailed):
            v.val_limit()('')

        with self.assertRaises(ValidationFailed):
            v.val_limit()(None)

    def test_limit_marker(self):

        positive_cases, negative_cases = self.cases_with_none_okay()

        for limit in positive_cases:
            limit_req = TestRulesBase.build_request(params=[('limit',
                                                             limit)])
            self.assertTrue(self.utilize_request(limit_req))

        for limit in negative_cases:
            limit_req = TestRulesBase.build_request(params=[('limit',
                                                             limit)])
            with self.assertRaises(errors.HTTPNotFound):
                self.utilize_request(limit_req, raiseme=True)


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

    def test_projectid_marker(self):

        positive_cases, negative_cases = self.cases_with_none_okay()

        for projectid in positive_cases:
            projectid_req = TestRulesBase.build_request(params=[('marker',
                                                        projectid)])
            self.assertTrue(self.utilize_request(projectid_req))

        for projectid in negative_cases:
            projectid_req = TestRulesBase.build_request(params=[('marker',
                                                        projectid)])
            with self.assertRaises(errors.HTTPBadRequestAPI):
                self.utilize_request(projectid_req, raiseme=True)
