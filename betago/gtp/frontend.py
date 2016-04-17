import sys

from .board import *
from .command import *
from .response import *

__all__ = [
    'GTPFrontend',
]


def _parse_command(gtp_command):
    pieces = gtp_command.split()
    name, args = pieces[0], pieces[1:]
    return Command(name, args)


def _serialize_response(gtp_response):
    return '%s %s\n\n' % (
        '=' if gtp_response.success else '?',
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
            response = self.process(command)
            self._output.write(_serialize_response(response))
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
        response = handler(*command.args)
        return response

    def ignore(self, *args):
        """Placeholder for commands we haven't dealt with yet."""
        return Success()

    def handle_known_command(self, command_name):
        # TODO Should actually check if the command is known.
        return Success('false')

    def handle_play(self, player, move):
        if player != 'white':
            return Error('Can only play as black')
        if move == 'pass':
            self._will_pass = True
        else:
            self.bot.apply_move(gtp_position_to_coords(move))
        return Success()

    def handle_genmove(self, player):
        if player != 'black':
            return Error('Can only play as white')
        if self._will_pass:
            return Success('pass')
        move = self.bot.select_move()
        return Success(coords_to_gtp_position(move))

    def handle_boardsize(self, size):
        if int(size) != 19:
            return Error('Only 19x19 currently supported')
        return Success()

    def handle_quit(self):
        self._stopped = True
        return Success()

    def handle_unknown(self, *args):
        return Error('Unrecognized command')
