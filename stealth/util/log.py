#
# Copyright (c) 2015 Xuan Yu xuanyu1@gmail.com
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import logging
from logging.config import dictConfig
from stealth.common import local
from stealth import config
_loggers = {}


def setup():
    log_config = config.dict()
    log_config.update({'version': 1})
    dictConfig(log_config)


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
        _loggers[name] = ContextAdapter(logging.getLogger(name), extra={})
    setup()
    return _loggers[name]
