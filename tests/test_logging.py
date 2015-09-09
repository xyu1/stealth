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
from testfixtures import LogCapture

from tests import V1Base
from stealth.util import log as logging


class TestLogging(V1Base):

    def setUp(self):
        super(TestLogging, self).setUp()

        self._hdrs = {"X-Auth-Token": self.create_project_id()}

    def _testuuid(self, request_id):
        try:
            uuid.UUID(request_id.replace(request_id[:4], ''))
        except ValueError:
            return False
        else:
            return True

    def test_logging_handler(self):
        self.simulate_get('/list', headers=self._hdrs)

        # NOTE(TheSriram): Create a new LOG handler, and make sure the
        # the next time we try to create one, we receive the one created
        # earlier.

        LOG_new = logging.getLogger(__name__)
        LOG_exists = logging.getLogger(__name__)

        self.assertEqual(LOG_new, LOG_exists)

    def test_logging_withoutcontext(self):

        LOG = logging.getLogger(__name__)
        with LogCapture() as capture:
            LOG.info("Testing Request ID outside wsgi call")
