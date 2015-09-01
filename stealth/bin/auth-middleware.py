#!/usr/bin/env python
import falcon
from stealth.impl_rax import auth_endpoint
from stealth.impl_rax import auth_app
from stealth.impl_rax import auth_mw
from oslo_config import cfg


def example_app(env, start_response):
    start_response('204 No Content', [])
    return []


CONF = cfg.CONF
CONF(project='mywsgiapp', args=[])
auth_mw.configure(CONF)

auth_redis_client = auth_endpoint.get_auth_redis_client()

app = auth_mw.wrap(example_app, auth_redis_client)
