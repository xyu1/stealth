import logging
from logging.config import dictConfig
from stealth import config
_loggers = {}


def setup():
    log_config = config.dict()
    log_config.update({'version': 1})
    # TMP TMP TMP TMP TMP TMP
    # dictConfig(log_config)
    # TMP TMP TMP TMP TMP TMP


def getLogger(name):
    if name not in _loggers:
        _loggers[name] = logging.getLogger()
    return _loggers[name]
