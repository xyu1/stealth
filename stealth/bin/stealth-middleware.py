#!/usr/bin/env python

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

import falcon
from stealth.impl_rax import auth_token
from stealth.impl_rax import auth_token_cache
from stealth.impl_rax import token_validation
from stealth.impl_rax import auth_middleware


# Need to replace with the real app.  This one is only an example.
def example_app(env, start_response):
    start_response('204 No Content', [])
    return []


auth_redis_client = token_validation.get_auth_redis_client()

app = auth_middleware.wrap(example_app, auth_redis_client)
