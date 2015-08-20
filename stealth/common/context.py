import uuid


class RequestContext(object):

    """Helper class to represent useful information about a request context.

    Stores information about request id per request made.
    """

    def __init__(self):
        self.request_id = 'req-' + str(uuid.uuid4())
