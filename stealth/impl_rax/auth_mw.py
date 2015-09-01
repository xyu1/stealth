from stealth.impl_rax import auth_endpoint
from stealth.impl_rax import auth_app

from oslo_config import cfg
_CONF = cfg.CONF

def configure(config):
    global _CONF
    ##global LOG

    _CONF = config
    _CONF.register_opts(AUTH_OPTIONS, group=AUTH_GROUP_NAME)
    _CONF.register_opts(REDIS_OPTIONS, group=REDIS_GROUP_NAME)

    ##logging.register(_CONF, AUTH_GROUP_NAME)
    ##logging.setup(_CONF, AUTH_GROUP_NAME)
    ##LOG = logging.getLogger(__name__)


def wrap(app, redis_client):
    """Wrap a WSGI app with Authentication middleware.

    Takes configuration from oslo.config.cfg.CONF.
    Requires auth.configure() be called first

    :param app: WSGI app to wrap
    :param redis_client: redis.Redis object connected to the redis cache

    :returns: a new  WSGI app that wraps the original
    """

    group = _CONF[AUTH_GROUP_NAME]
    auth_url = group['auth_url']
    blacklist_ttl = group['blacklist_ttl']
    max_cache_life = group['max_cache_life']

    LOG.debug('Auth URL: {0:}'.format(auth_url))

    def middleware(env, start_response):
        try:
            token = env['HTTP_X_AUTH_TOKEN']
            tenant = env['HTTP_X_PROJECT_ID']

            # validate the client and fill out the environment it's valid
            if _validate_client(redis_client,
                                auth_url,
                                tenant,
                                token,
                                env,
                                blacklist_ttl,
                                max_cache_life):
                LOG.debug(_('Auth Token validated.'))
                return app(env, start_response)

            else:
                # Validation failed for some reason, just error out as a 401
                LOG.error(_('Auth Token validation failed.'))
                return _http_unauthorized(start_response)
        except (KeyError, LookupError):
            # Header failure, error out with 412
            LOG.error(_('Missing required headers.'))
            return _http_precondition_failed(start_response)
    return middleware
