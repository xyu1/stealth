import logging
import falcon
import stealth.util.auth_endpoint as auth
import stealth.util.log as logging
from stealth.transport.wsgi import errors
from stealth import conf
logger = logging.getLogger(__name__)


# Get the separated Redis Server for Auth
auth_redis_client = auth.get_auth_redis_client()

authserv = auth.AuthServ(auth_redis_client)


class ItemResource(object):

    def on_get(self, req, resp, project_id):
        resp.location = '/auth/%s' % (project_id)
        logger.info('Auth [{0}]... '.format(project_id))
        res, err = authserv.auth(req, resp, project_id)
        if res is False:
            raise errors.HTTPUnauthorizedError(err)
        resp.status = falcon.HTTP_204  # This is the default status
