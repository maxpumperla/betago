__all__ = [
    'Response',
    'Success',
    'Error',
]


class Response(object):
    """Response to a GTP command."""
    def __init__(self, status, body):
        self.success = status
        self.body = body


class Success(Response):
    def __init__(self, body=''):
        super(Success, self).__init__(True, body)


class Error(Response):
    def __init__(self, error_message=''):
        super(Error, self).__init__(False, error_message)
