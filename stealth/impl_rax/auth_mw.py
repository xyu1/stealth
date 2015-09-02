from stealth.impl_rax.auth_endpoint import AdminToken, \
    LOG, _validate_client_impersonation, _validate_client_token
from stealth import conf


def _http_precondition_failed(start_response):
    """Responds with HTTP 412."""
    start_response('412 Precondition Failed', [('Content-Length', '0')])
    return []


def _http_unauthorized(start_response):
    """Responds with HTTP 401."""
    start_response('401 Unauthorized', [('Content-Length', '0')])
    return []


def wrap(app, redis_client):
    """Wrap a WSGI app with Authentication middleware.

    :param app: WSGI app to wrap
    :param redis_client: redis.Redis object connected to the redis cache

    :returns: a new  WSGI app that wraps the original
    """

    auth_url = conf.auth.auth_url
    admin_name = conf.auth.admin_name
    admin_pass = conf.auth.admin_pass
    Admintoken = AdminToken(auth_url, admin_name, admin_pass)

    # TODO:
    # blacklist_ttl = conf.'blacklist_ttl'
    # max_cache_life = conf.'max_cache_life'

    def middleware(env, start_response):
        try:
            project_id = env['HTTP_X_PROJECT_ID']
            token = ''
            valid = False

            if 'HTTP_X_AUTH_TOKEN' in env:
                token = env['HTTP_X_AUTH_TOKEN']

            valid, token = _validate_client_token(redis_client,
                auth_url, project_id, token)

            if not valid:
                valid, Usertoken, cache_key = _validate_client_impersonation(redis_client,
                    auth_url, project_id, Admintoken)
                if valid and Usertoken and Usertoken['token']:
                    token = Usertoken['token']
                    env['HTTP_X_AUTH_TOKEN'] = token

            # validate the client and fill out the environment it's valid
            if valid:
                LOG.debug(('Middleware: Auth Token validated.'))
                return app(env, start_response)

            else:
                # Validation failed for some reason, just error out as a 401
                LOG.error(('Middleware: Auth Token validation failed.'))
                return _http_unauthorized(start_response)
        except (KeyError, LookupError):
            # Header failure, error out with 412
            LOG.error(('Middleware: Missing required headers.'))
            return _http_precondition_failed(start_response)

    return middleware
