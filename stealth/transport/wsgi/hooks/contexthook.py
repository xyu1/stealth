import stealth


def ContextHook(req, resp, params):
    from threading import local as local_factory
    stealth.context = local_factory()
