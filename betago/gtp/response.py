__all__ = [
    'Response',
    'error',
    'success',
]


class Response(object):
    """Response to a GTP command."""
    def __init__(self, status, body):
        self.success = status
        self.body = body


def success(body=''):
    """Make a successful GTP response."""
    return Response(status=True, body=body)


def error(body=''):
    """Make an error GTP response."""
    return Response(status=False, body=body)
