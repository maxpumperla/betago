import sys

from . import response
from .board import *
from .command import *

__all__ = [
    'GTPFrontend',
]


def _parse_command(gtp_command):
    pieces = gtp_command.split()
    # GTP commands may include an optional sequence number. If it's
    # provided, we must include it in the response.
    try:
        sequence = int(pieces[0])
        pieces = pieces[1:]
    except ValueError:
        sequence = None
    name, args = pieces[0], pieces[1:]
    return Command(sequence, name, args)


def _serialize_response(gtp_command, gtp_response):
    return '%s%s %s\n\n' % (
        '=' if gtp_response.success else '?',
        '' if gtp_command.sequence is None else str(gtp_command.sequence),
        gtp_response.body,
    )


class GTPFrontend(object):
    """Go Text Protocol frontend for a bot.

    Handles parsing GTP commands and formatting responses.

    Extremely limited implementation right now:
     - Only supports 19x19 boards.
     - Doesn't support handicap.
     - Can only play as black.
     - When white passes, black will pass too.
    """
    def __init__(self, bot):
        self.bot = bot
        self._input = sys.stdin
        self._output = sys.stdout
        self._stopped = False
        self._will_pass = False

    def run(self):
        while not self._stopped:
            ln = self._input.readline().strip()
            command = _parse_command(ln)
            resp = self.process(command)
            self._output.write(_serialize_response(command, resp))
            self._output.flush()

    def process(self, command):
        handlers = {
            'boardsize': self.handle_boardsize,
            'clear_board': self.ignore,
            'genmove': self.handle_genmove,
            'known_command': self.handle_known_command,
            'komi': self.ignore,
            'play': self.handle_play,
            'quit': self.handle_quit,
        }
        handler = handlers.get(command.name, self.handle_unknown)
        resp = handler(*command.args)
        return resp

    def ignore(self, *args):
        """Placeholder for commands we haven't dealt with yet."""
        return response.success()

    def handle_known_command(self, command_name):
        # TODO Should actually check if the command is known.
        return response.success('false')

    def handle_play(self, player, move):
        if player != 'white':
            return Error('Can only play as black')
        if move == 'pass':
            self._will_pass = True
        else:
            self.bot.apply_move(gtp_position_to_coords(move))
        return response.success()

    def handle_genmove(self, player):
        if player != 'black':
            return response.error('Can only play as black')
        # TODO The bot should decide when the pass.
        if self._will_pass:
            return response.success('pass')
        move = self.bot.select_move()
        return response.success(coords_to_gtp_position(move))

    def handle_boardsize(self, size):
        if int(size) != 19:
            return response.error('Only 19x19 currently supported')
        return response.success()

    def handle_quit(self):
        self._stopped = True
        return response.success()

    def handle_unknown(self, *args):
        return response.error('Unrecognized command')
