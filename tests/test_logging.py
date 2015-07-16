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
        self.assertFalse(self._testuuid(capture.records[0].request_id))
