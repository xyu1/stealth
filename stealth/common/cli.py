

import functools
import sys


import stealth.util.log as logging


LOG = logging.getLogger(__name__)


def _fail(returncode, ex):
    """Handles terminal errors.

    :param returncode: process return code to pass to sys.exit
    :param ex: the error that occurred
    """

    LOG.exception(ex)
    sys.exit(returncode)


def runnable(func):
    """Entry point wrapper.

    Note: This call blocks until the process is killed
          or interrupted.
    """

    @functools.wraps(func)
    def _wrapper():
        try:
            func()
        except KeyboardInterrupt:
            LOG.info(u'Terminating')
        except Exception as ex:
            _fail(1, ex)

    return _wrapper
