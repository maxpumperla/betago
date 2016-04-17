__all__ = [
    'Command',
]


class Command(object):
    """A GTP command.

    Example:
    'play white B15' becomes Command('play', ('white', 'B15'))
    """
    def __init__(self, name, args):
        self.name = name
        self.args = tuple(args)

    def __repr__(self):
        return 'Command(%r, %r)' % (self.name, self.args)
