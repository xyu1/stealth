#!/usr/bin/env python
import falcon
from stealth.impl_rax import auth_token
from stealth.impl_rax import auth_token_cache
from stealth.impl_rax import auth_mw


def example_app(env, start_response):
    start_response('204 No Content', [])
    return []


auth_redis_client = auth_token_cache.get_auth_redis_client()

app = auth_mw.wrap(example_app, auth_redis_client)
