import logging
from logging.config import dictConfig
from stealth.common import local
from stealth import config
_loggers = {}


def setup():
    log_config = config.dict()
    log_config.update({'version': 1})
    # TMP TMP TMP TMP TMP TMP
    # dictConfig(log_config)
    # TMP TMP TMP TMP TMP TMP


class ContextAdapter(logging.LoggerAdapter):

    def process(self, msg, kwargs):
        context = getattr(local.store, 'context', None)
        if context:
            kwargs['extra'] = {'request_id': context.request_id}
        else:
            kwargs['extra'] = {'request_id': 'Not in wsgi __call__'}
        self.extra = kwargs['extra']
        return msg, kwargs


def getLogger(name):
    if name not in _loggers:
        _loggers[name] = ContextAdapter(logging.getLogger(), extra={})
    return _loggers[name]
