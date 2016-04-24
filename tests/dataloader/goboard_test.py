import unittest

from betago.dataloader.goboard import GoBoard, from_string, to_string


class GoBoardTest(unittest.TestCase):
    def test_is_move_legal(self):
        board = GoBoard()
        board.apply_move('b', (4, 4))

        self.assertTrue(board.is_move_legal('b', (3, 3)))
        self.assertTrue(board.is_move_legal('w', (3, 3)))

    def test_is_move_legal_occupied(self):
        board = GoBoard()
        board.apply_move('b', (4, 4))

        self.assertFalse(board.is_move_legal('b', (4, 4)))
        self.assertFalse(board.is_move_legal('w', (4, 4)))

    def test_is_move_legal_suicide(self):
        board = GoBoard()
        # Make a ponnuki.
        board.apply_move('b', (4, 4))
        board.apply_move('b', (5, 5))
        board.apply_move('b', (6, 4))
        board.apply_move('b', (5, 3))

        # White can't move in the center.
        self.assertFalse(board.is_move_legal('w', (5, 4)))
        # But Black can.
        self.assertTrue(board.is_move_legal('b', (5, 4)))

    def test_is_move_legal_capture_not_suicide(self):
        board = GoBoard()
        # Set up a ko.
        board.apply_move('b', (4, 4))
        board.apply_move('b', (5, 5))
        board.apply_move('b', (6, 4))
        board.apply_move('b', (5, 3))
        board.apply_move('w', (4, 5))
        board.apply_move('w', (5, 6))
        board.apply_move('w', (6, 5))

        # Either can move in the center.
        self.assertTrue(board.is_move_legal('w', (5, 4)))
        self.assertTrue(board.is_move_legal('b', (5, 4)))

    def test_is_move_legal_should_not_mutate_board(self):
        board = GoBoard()
        board.apply_move('b', (4, 4))

        board.is_move_legal('b', (4, 5))

        # Check the board.
        self.assertFalse(board.is_move_on_board((4, 5)))
        # Check the go strings as well.
        group = board.go_strings[4, 4]
        self.assertEqual(1, group.get_num_stones())
        self.assertEqual(4, group.get_num_liberties())

    def test_is_move_legal_ko(self):
        board = GoBoard()
        # Set up a ko.
        board.apply_move('b', (4, 4))
        board.apply_move('b', (5, 5))
        board.apply_move('b', (6, 4))
        board.apply_move('b', (5, 3))
        board.apply_move('w', (4, 5))
        board.apply_move('w', (5, 6))
        board.apply_move('w', (6, 5))
        # White captures.
        board.apply_move('w', (5, 4))

        # Black can't fill in the ko.
        self.assertTrue(board.is_simple_ko('b', (5, 5)))
        self.assertFalse(board.is_move_legal('b', (5, 5)))
        # But white can.
        self.assertTrue(board.is_move_legal('w', (5, 5)))

    def test_from_string(self):
        board = from_string('''
            .b...
            bb...
            .....
            ..www
            ..w..
        ''')

        self.assertEqual(5, board.board_size)
        self.assertNotIn((4, 0), board.board)
        self.assertEqual('b', board.board[4, 1])
        self.assertNotIn((4, 2), board.board)
        self.assertNotIn((1, 0), board.board)
        self.assertNotIn((1, 1), board.board)
        self.assertEqual('w', board.board[1, 2])
        self.assertEqual('w', board.board[0, 2])

    def test_to_string(self):
        board = GoBoard(5)
        for move in [(3, 0), (3, 1), (4, 1)]:
            board.apply_move('b', move)
        for move in [(0, 2), (1, 2), (1, 3), (1, 4)]:
            board.apply_move('w', move)

        board_string = to_string(board)
        lines = board_string.split('\n')
        self.assertEqual([
            '.b...',
            'bb...',
            '.....',
            '..www',
            '..w..',
        ], lines)
