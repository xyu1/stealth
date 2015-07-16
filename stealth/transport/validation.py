import re

import falcon
from stoplight import Rule, ValidationFailed, validation_function

from stealth.transport.wsgi import errors


VAULT_ID_MAX_LEN = 128
VAULT_ID_REGEX = re.compile('^[a-zA-Z0-9_\-]+$')
BLOCK_ID_REGEX = re.compile('\\b[0-9a-f]{40}\\b')
UUID_REGEX = re.compile(
    '[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}')
FILE_ID_REGEX = UUID_REGEX
STORAGE_BLOCK_ID_REGEX = re.compile(
    '[0-9a-f]{40}_[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}'
)
OFFSET_REGEX = re.compile(
    '(?<![-.])\\b[0-9]+\\b(?!\\.[0-9])')
LIMIT_REGEX = re.compile(
    '(?<![-.])\\b[0-9]+\\b(?!\\.[0-9])')

PROJECTID_REGEX = re.compile('^[0-9]{6,7}$')


@validation_function
def val_vault_id(value):
    if not VAULT_ID_REGEX.match(value):
        raise ValidationFailed('Invalid vault id {0}'.format(value))

    if len(value) > VAULT_ID_MAX_LEN:
        raise ValidationFailed('Vault ID exceeded max len {0}'.format(
            VAULT_ID_MAX_LEN))


@validation_function
def val_block_id(value):
    if not BLOCK_ID_REGEX.match(value):
        raise ValidationFailed('Invalid Block ID {0}'.format(value))


@validation_function
def val_storage_block_id(value):
    if not STORAGE_BLOCK_ID_REGEX.match(value):
        raise ValidationFailed('Invalid Storage Block ID {0}'.format(value))


@validation_function
def val_file_id(value):
    if not FILE_ID_REGEX.match(value):
        raise ValidationFailed('Invalid File ID {0}'.format(value))


@validation_function
def val_offset(value):
    if not OFFSET_REGEX.match(value):
        raise ValidationFailed('Invalid offset {0}'.format(value))


@validation_function
def val_limit(value):
    if not LIMIT_REGEX.match(value):
        raise ValidationFailed('Invalid limit {0}'.format(value))


@validation_function
def val_projectid(value):
    if not PROJECTID_REGEX.match(value):
        raise ValidationFailed('Invalid ProjectID {0}'.format(value))


@validation_function
def is_request(value):
    if not isinstance(value, falcon.request.Request):
        raise ValidationFailed('Input must be a request')


def _abort(status_code):
    abort_errors = {
        400: errors.HTTPBadRequestAPI('Invalid Request'),
        404: errors.HTTPNotFound,
        500: errors.HTTPInternalServerError
    }
    raise abort_errors[status_code]


class RequestRule(Rule):

    def __init__(self, *nested_rules):
        """Constructs a new Rule for validating requests. Any
        nested rules needed for validating parts of the request
        (such as headers, query string params, etc) should
        also be passed in.

        :param nested_rules: Any sub rules that also should be
          used for validation
        """
        # If we get something that's not a request here,
        # something bad happened in the server (i.e.
        # maybe a programming error), so return a 500

        # NOTE(TheSriram): One should not be creating a generic empty
        # RequestRule, a list of rules always needs to be passed in as
        # arguments.
        # Example: RequestRule(OffsetMarkerRule, LimitRule)
        Rule.__init__(self,
                      vfunc=is_request(none_ok=True),  # pragma: no cover
                      errfunc=lambda: _abort(500),
                      nested_rules=list(nested_rules))


class QueryStringRule(Rule):

    def __init__(self, querystring_name, vfunc, errfunc):
        getter = lambda req: req.get_param(querystring_name)
        Rule.__init__(self, vfunc=vfunc, getter=getter, errfunc=errfunc)

# parameter rules

VaultGetRule = Rule(val_vault_id(), lambda: _abort(404))
VaultPutRule = Rule(val_vault_id(), lambda: _abort(400))
BlockGetRule = Rule(val_block_id(), lambda: _abort(404))
BlockPutRule = Rule(val_block_id(), lambda: _abort(400))
BlockPostRule = Rule(val_block_id(), lambda: _abort(400))
StorageBlockGetRule = Rule(val_storage_block_id(), lambda: _abort(404))
StorageBlockPutRule = Rule(val_storage_block_id(), lambda: _abort(400))
FileGetRule = Rule(val_file_id(), lambda: _abort(404))
FilePutRule = Rule(val_file_id(), lambda: _abort(400))
FilePostRule = Rule(val_file_id(), lambda: _abort(400))
FileGetRuleNoneOk = Rule(val_file_id(none_ok=True), lambda: _abort(404))
FilePutRuleNoneOk = Rule(val_file_id(none_ok=True), lambda: _abort(400))
FilePostRuleNoneOk = Rule(val_file_id(none_ok=True), lambda: _abort(400))
BlockGetRuleNoneOk = Rule(val_block_id(none_ok=True), lambda: _abort(404))
BlockPutRuleNoneOk = Rule(val_block_id(none_ok=True), lambda: _abort(400))
BlockPostRuleNoneOk = Rule(val_block_id(none_ok=True), lambda: _abort(400))
StorageBlockRuleGetNoneOk = Rule(val_storage_block_id(none_ok=True),
                                 lambda: _abort(404))
StorageBlockRulePutNoneOk = Rule(val_storage_block_id(none_ok=True),
                                 lambda: _abort(400))

# query string rules
ProjectIDRule = QueryStringRule("marker", val_projectid(none_ok=True),
                                lambda: _abort(400))

LimitRule = QueryStringRule("limit", val_limit(none_ok=True),
                            lambda: _abort(404))

FileMarkerRule = QueryStringRule("marker", val_file_id(none_ok=True),
                                 lambda: _abort(404))

OffsetMarkerRule = QueryStringRule("marker", val_offset(none_ok=True),
                                   lambda: _abort(404))

BlockMarkerRule = QueryStringRule("marker", val_block_id(none_ok=True),
                                  lambda: _abort(404))

StorageBlockMarkerRule = QueryStringRule("marker",
                                         val_storage_block_id(none_ok=True),
                                         lambda: _abort(404))
