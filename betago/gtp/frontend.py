import sys

from . import command, response
from .board import *

__all__ = [
    'GTPFrontend',
]


class GTPFrontend(object):
    """Go Text Protocol frontend for a bot.

    Handles parsing GTP commands and formatting responses.

    Extremely limited implementation right now:
     - Only supports 19x19 boards.
     - Doesn't support handicap.
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
            cmd = command.parse(ln)
            resp = self.process(cmd)
            self._output.write(response.serialize(cmd, resp))
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
        color = 'b' if player == 'black' else 'w'
        if move == 'pass':
            self._will_pass = True
        else:
            self.bot.apply_move(color, gtp_position_to_coords(move))
        return response.success()

    def handle_genmove(self, player):
        bot_color = 'b' if player == 'black' else 'w'
        # TODO The bot should decide when the pass.
        if self._will_pass:
            return response.success('pass')
        move = self.bot.select_move(bot_color)
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
