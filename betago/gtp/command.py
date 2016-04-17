__all__ = [
    'Command',
]


class Command(object):
    """A GTP command.

    Example:
    '5 play white B15' becomes Command(5, 'play', ('white', 'B15'))
    """
    def __init__(self, sequence, name, args):
        self.sequence = sequence
        self.name = name
        self.args = tuple(args)

    def __repr__(self):
        return 'Command(%r, %r, %r)' % (self.sequence, self.name, self.args)
