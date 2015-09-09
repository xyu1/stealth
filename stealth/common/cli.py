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
