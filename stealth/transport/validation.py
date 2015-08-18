import re

import falcon
from stealth.transport.wsgi import errors

from stoplight import Rule, ValidationFailed, validation_function


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
def val_projectid(value):
    if not PROJECTID_REGEX.match(value):
        raise ValidationFailed('Invalid ProjectID {0}'.format(value))
