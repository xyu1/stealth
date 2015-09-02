import stealth
from stealth.impl_rax.auth_token import AdminToken
from stealth.impl_rax.auth_token_cache import \
    _validate_client_impersonation, _validate_client_token
from stealth import conf
from stealth.common import context
from stealth.common import local

import stealth.util.log as logging

LOG = logging.getLogger(__name__)


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

    from threading import local as local_factory
    stealth.context = local_factory()

    # TODO:
    # blacklist_ttl = conf.'blacklist_ttl'
    # max_cache_life = conf.'max_cache_life'

    def middleware(env, start_response):

        # Inject transaction-id into the response headers.
        def transactionhook(status, headers, exc_info=None):
            transaction = context.RequestContext()
            setattr(local.store, 'context', transaction)
            stealth.context.transaction = transaction
            headers.append(('Transaction-ID', str(
                stealth.context.transaction.request_id)))
            return start_response(status, headers, exc_info)

        try:
            project_id = env['HTTP_X_PROJECT_ID']
            token = ''
            cache_key = ''
            valid = False

            if 'HTTP_X_AUTH_TOKEN' in env:
                cache_key = env['HTTP_X_AUTH_TOKEN']

            # Validate the input cache_key.
            valid, token = _validate_client_token(redis_client,
                auth_url, project_id, cache_key)
            if valid:
                env['X-AUTH-TOKEN'] = token
                env.pop('HTTP_X_AUTH_TOKEN', cache_key)
                return app(env, transactionhook)

            # Validate the client with the impersonation token
            valid, usertoken, cache_key = _validate_client_impersonation(
                redis_client, auth_url, project_id, Admintoken)
            if valid and usertoken and usertoken['token']:

                # Inject cahce_key as the auth token into the response headers.
                def custom_start_response(status, headers, exc_info=None):
                    headers.append(('HTTP_X_AUTH_TOKEN', str(cache_key)))
                    return transactionhook(status, headers, exc_info)

                token = usertoken['token']
                env['X-AUTH-TOKEN'] = token
                LOG.debug(('Middleware: Auth Token validated.'))
                return app(env, custom_start_response)

            else:
                # Validation failed for some reason, just error out as a 401
                LOG.error(('Middleware: Auth Token validation failed.'))
                return _http_unauthorized(start_response)
        except (KeyError, LookupError):
            # Header failure, error out with 412
            LOG.error(('Middleware: Missing required headers.'))
            return _http_precondition_failed(start_response)

    return middleware
