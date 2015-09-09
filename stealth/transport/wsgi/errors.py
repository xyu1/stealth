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
import falcon.status_codes as status


# class HTTPInternalServerError(falcon.HTTPInternalServerError):

#     """Wraps falcon.HTTPServiceUnavailable"""

#     TITLE = u'Service temporarily unavailable'

#     def __init__(self, description, **kwargs):
#         super(HTTPInternalServerError, self).__init__(
#             self.TITLE, description=description, **kwargs)


class HTTPUnauthorizedError(falcon.HTTPUnauthorized):

    """Wraps falcon.HTTPUnauthorized"""

    TITLE = u'The user is Unauthorized'

    def __init__(self, description, **kwargs):
        super(HTTPUnauthorizedError, self).__init__(
            self.TITLE, description=description, **kwargs)


# class HTTPBadGateway(falcon.HTTPBadGateway):

#     """Wraps falcon.HTTPServiceUnavailable"""

#     TITLE = u'Bad Gateway'

#     def __init__(self, description):
#         super(HTTPBadGateway, self).__init__(
#             self.TITLE, description=description)


# class HTTPBadRequestAPI(falcon.HTTPBadRequest):

#     """Wraps falcon.HTTPBadRequest with a contextual title."""

#     TITLE = u'Invalid API request'

#     def __init__(self, description):
#         super(HTTPBadRequestAPI, self).__init__(self.TITLE, description)


class HTTPBadRequestBody(falcon.HTTPBadRequest):

    """Wraps falcon.HTTPBadRequest with a contextual title."""

    TITLE = u'Invalid request body'

    def __init__(self, description):
        super(HTTPBadRequestBody, self).__init__(self.TITLE, description)


# class HTTPConflict(falcon.HTTPConflict):

#     """Wraps falcon.HTTPConflict with a contextual title."""

#     TITLE = u'Conflict'

#     def __init__(self, description):
#         super(HTTPConflict, self).__init__(self.TITLE, description)


# class HTTPPreconditionFailed(falcon.HTTPPreconditionFailed):

#     """Wraps HTTPPreconditionFailed with a contextual title."""

#     TITLE = u'Precondition Failure'

#     def __init__(self, description):
#         super(HTTPPreconditionFailed, self).__init__(self.TITLE, description)


# class HTTPNotFound(falcon.HTTPNotFound):

#     """Wraps falcon.HTTPNotFound"""

#     def __init__(self):
#         super(HTTPNotFound, self).__init__()


# class HTTPMethodNotAllowed(falcon.HTTPMethodNotAllowed):

#     """Wraps falcon.HTTPMethodNotAllowed"""

#     TITLE = u'Method Not Allowed'

#     def __init__(self, allowed_method, description):
#         super(HTTPMethodNotAllowed, self).__init__(allowed_method,
#                                                   description=description)
