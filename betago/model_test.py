import unittest

from . import model
from .dataloader import goboard


class ModelTestCase(unittest.TestCase):
    def test_all_empty_points(self):
        board = goboard.from_string('''
            .b.
            bb.
            .ww
        ''')

        empty_points = model.all_empty_points(board)

        self.assertItemsEqual(
            [(0, 0), (1, 2), (2, 0), (2, 2)],
            empty_points)

    def test_get_first_valid_move(self):
        board = goboard.from_string('''
            .b.
            bb.
            .ww
        ''')
        candidates = [(0, 1), (1, 0), (2, 0), (2, 2)]

        self.assertEqual((2, 0), model.get_first_valid_move(board, 'b', candidates))
        self.assertEqual((2, 2), model.get_first_valid_move(board, 'w', candidates))
