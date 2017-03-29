# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file, You can
# obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import absolute_import
import copy
from six.moves import range


class GoBoard(object):
    '''
    Representation of a go board. It contains "GoStrings" to represent stones and liberties. Moreover,
    the board can account for ko and handle captured stones.
    '''
    def __init__(self, board_size=19):
        '''
        Parameters
        ----------
        ko_last_move_num_captured: How many stones have been captured last move. If this is not 1, it can't be ko.
        ko_last_move: board position of the ko.
        board_size: Side length of the board, defaulting to 19.
        go_strings: Dictionary of go_string objects representing stones and liberties.
        '''
        self.ko_last_move_num_captured = 0
        self.ko_last_move = -3
        self.board_size = board_size
        self.board = {}
        self.go_strings = {}

    def fold_go_strings(self, target, source, join_position):
        ''' Merge two go strings by joining their common moves'''
        if target == source:
            return
        for stone_position in source.stones.stones:
            self.go_strings[stone_position] = target
            target.insert_stone(stone_position)
        target.copy_liberties_from(source)
        target.remove_liberty(join_position)

    def add_adjacent_liberty(self, pos, go_string):
        '''
        Append new liberties to provided GoString for the current move
        '''
        row, col = pos
        if row < 0 or col < 0 or row > self.board_size - 1 or col > self.board_size - 1:
            return
        if pos not in self.board:
            go_string.insert_liberty(pos)

    def is_move_on_board(self, move):
        return move in self.board

    def is_move_suicide(self, color, pos):
        '''Check if a proposed move would be suicide.'''
        # Make a copy of ourself to apply the move.
        temp_board = copy.deepcopy(self)
        temp_board.apply_move(color, pos)
        new_string = temp_board.go_strings[pos]
        return new_string.get_num_liberties() == 0

    def is_move_legal(self, color, pos):
        '''Check if a proposed moved is legal.'''
        return (not self.is_move_on_board(pos)) and \
            (not self.is_move_suicide(color, pos)) and \
            (not self.is_simple_ko(color, pos))

    def create_go_string(self, color, pos):
        ''' Create GoString from current Board and move '''
        go_string = GoString(self.board_size, color)
        go_string.insert_stone(pos)
        self.go_strings[pos] = go_string
        self.board[pos] = color

        row, col = pos
        for adjpos in [(row - 1, col), (row + 1, col), (row, col - 1), (row, col + 1)]:
            self.add_adjacent_liberty(adjpos, go_string)
        return go_string

    def other_color(self, color):
        '''
        Color of other player
        '''
        if color == 'b':
            return 'w'
        if color == 'w':
            return 'b'

    def is_simple_ko(self, play_color, pos):
        '''
        Determine ko from board position and player.

        Parameters:
        -----------
        play_color: Color of the player to make the next move.
        pos: Current move as (row, col)
        '''
        enemy_color = self.other_color(play_color)
        row, col = pos
        if self.ko_last_move_num_captured == 1:
            last_move_row, last_move_col = self.ko_last_move
            manhattan_distance_last_move = abs(last_move_row - row) + abs(last_move_col - col)
            if manhattan_distance_last_move == 1:
                last_go_string = self.go_strings.get((last_move_row, last_move_col))
                if last_go_string is not None and last_go_string.get_num_liberties() == 1:
                    if last_go_string.get_num_stones() == 1:
                        num_adjacent_enemy_liberties = 0
                        for adjpos in [(row - 1, col), (row + 1, col), (row, col - 1), (row, col + 1)]:
                            if (self.board.get(adjpos) == enemy_color and
                               self.go_strings[adjpos].get_num_liberties() == 1):
                                num_adjacent_enemy_liberties = num_adjacent_enemy_liberties + 1
                        if num_adjacent_enemy_liberties == 1:
                            return True
        return False

    def check_enemy_liberty(self, play_color, enemy_pos, our_pos):
        '''
        Update surrounding liberties on board after a move has been played.

        Parameters:
        -----------
        play_color: Color of player about to move
        enemy_pos: latest enemy move
        our_pos: our latest move
        '''
        enemy_row, enemy_col = enemy_pos
        our_row, our_col = our_pos

        # Sanity checks
        if enemy_row < 0 or enemy_row >= self.board_size or enemy_col < 0 or enemy_col >= self.board_size:
            return
        enemy_color = self.other_color(play_color)
        if self.board.get(enemy_pos) != enemy_color:
            return
        enemy_string = self.go_strings[enemy_pos]
        if enemy_string is None:
            raise ValueError('Inconsistency between board and go_strings at %r' % enemy_pos)

        # Update adjacent liberties on board
        enemy_string.remove_liberty(our_pos)
        if enemy_string.get_num_liberties() == 0:
            for enemy_pos in enemy_string.stones.stones:
                string_row, string_col = enemy_pos
                del self.board[enemy_pos]
                del self.go_strings[enemy_pos]
                self.ko_last_move_num_captured = self.ko_last_move_num_captured + 1
                for adjstring in [(string_row - 1, string_col), (string_row + 1, string_col),
                                  (string_row, string_col - 1), (string_row, string_col + 1)]:
                    self.add_liberty_to_adjacent_string(adjstring, enemy_pos, play_color)

    def apply_move(self, play_color, pos):
        '''
        Execute move for given color, i.e. play current stone on this board
        Parameters:
        -----------
        play_color: Color of player about to move
        pos: Current move as (row, col)
        '''
        if pos in self.board:
            raise ValueError('Move ' + str(pos) + 'is already on board.')

        self.ko_last_move_num_captured = 0
        row, col = pos

        # Remove any enemy stones that no longer have a liberty
        self.check_enemy_liberty(play_color, (row - 1, col), pos)
        self.check_enemy_liberty(play_color, (row + 1, col), pos)
        self.check_enemy_liberty(play_color, (row, col - 1), pos)
        self.check_enemy_liberty(play_color, (row, col + 1), pos)

        # Create a GoString for our new stone, and merge with any adjacent strings
        play_string = self.create_go_string(play_color, pos)
        play_string = self.fold_our_moves(play_string, play_color, (row - 1, col), pos)
        play_string = self.fold_our_moves(play_string, play_color, (row + 1, col), pos)
        play_string = self.fold_our_moves(play_string, play_color, (row, col - 1), pos)
        play_string = self.fold_our_moves(play_string, play_color, (row, col + 1), pos)

        # Store last move for ko
        self.ko_last_move = pos

    def add_liberty_to_adjacent_string(self, string_pos, liberty_pos, color):
        ''' Insert liberty into corresponding GoString '''
        if self.board.get(string_pos) != color:
            return
        go_string = self.go_strings[string_pos]
        go_string.insert_liberty(liberty_pos)

    def fold_our_moves(self, first_string, color, pos, join_position):
        ''' Fold current board situation with a new move played by us'''
        row, col = pos
        if row < 0 or row >= self.board_size or col < 0 or col >= self.board_size:
            return first_string
        if self.board.get(pos) != color:
            return first_string
        string_to_fold = self.go_strings[pos]
        self.fold_go_strings(string_to_fold, first_string, join_position)
        return string_to_fold

    def __str__(self):
        result = 'GoBoard\n'
        for i in range(self.board_size - 1, -1, -1):
            line = ''
            for j in range(0, self.board_size):
                thispiece = self.board.get((i, j))
                if thispiece is None:
                    line = line + '.'
                if thispiece == 'b':
                    line = line + '*'
                if thispiece == 'w':
                    line = line + 'O'
            result = result + line + '\n'
        return result


class BoardSequence(object):
    '''
    Store a sequence of locations on a board, which could either represent stones or liberties.
    '''
    def __init__(self, board_size=19):
        self.board_size = board_size
        self.stones = []
        self.board = {}

    def insert(self, combo):
        row, col = combo
        if combo in self.board:
            return
        self.stones.append(combo)
        self.board[combo] = len(self.stones) - 1

    def erase(self, combo):
        if combo not in self.board:
            return
        iid = self.board[combo]
        if iid == len(self.stones) - 1:
            del self.stones[iid]
            del self.board[combo]
            return
        self.stones[iid] = self.stones[len(self.stones) - 1]
        del self.stones[len(self.stones) - 1]
        movedcombo = self.stones[iid]
        self.board[movedcombo] = iid
        del self.board[combo]

    def exists(self, combo):
        return combo in self.board

    def size(self):
        return len(self.stones)

    def __getitem__(self, iid):
        return self.stones[iid]

    def __str__(self):
        result = 'BoardSequence\n'
        for row in range(self.board_size - 1, -1, -1):
            thisline = ""
            for col in range(0, self.board_size):
                if self.exists((row, col)):
                    thisline = thisline + "*"
                else:
                    thisline = thisline + "."
            result = result + thisline + "\n"
        return result


class GoString(object):
    '''
    Represents a string of contiguous stones of one color on the board, including a list of all its liberties.
    '''
    def __init__(self, board_size, color):
        self.board_size = board_size
        self.color = color
        self.liberties = BoardSequence(board_size)
        self.stones = BoardSequence(board_size)

    def get_stone(self, index):
        return self.stones[index]

    def get_liberty(self, index):
        return self.liberties[index]

    def insert_stone(self, combo):
        self.stones.insert(combo)

    def get_num_stones(self):
        return self.stones.size()

    def remove_liberty(self, combo):
        self.liberties.erase(combo)

    def get_num_liberties(self):
        return self.liberties.size()

    def insert_liberty(self, combo):
        self.liberties.insert(combo)

    def copy_liberties_from(self, source):
        for libertyPos in source.liberties.stones:
            self.liberties.insert(libertyPos)

    def __str__(self):
        result = "go_string[ stones=" + str(self.stones) + " liberties=" + str(self.liberties) + " ]"
        return result


def from_string(board_string):
    """Build a board from an ascii-art representation.

    'b' for black stones
    'w' for white stones
    '.' for empty

    The bottom row is row 0, and the top row is row boardsize - 1. This
    matches the normal way you'd use board coordinates, with A1 in the
    bottom-left.

    Rows are separated by newlines. Extra whitespace is ignored.
    """
    rows = [line.strip() for line in board_string.strip().split("\n")]
    boardsize = len(rows)
    if any(len(row) != boardsize for row in rows):
        raise ValueError('Board must be square')

    board = GoBoard(boardsize)
    rows.reverse()
    for r, row_string in enumerate(rows):
        for c, point in enumerate(row_string):
            if point in ('b', 'w'):
                board.apply_move(point, (r, c))
    return board


def to_string(board):
    """Make an ascii-art representation of a board."""
    rows = []
    for r in range(board.board_size):
        row = ''
        for c in range(board.board_size):
            row += board.board.get((r, c), '.')
        rows.append(row)
    rows.reverse()
    return '\n'.join(rows)
