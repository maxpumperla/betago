import unittest

from betago import scoring
from betago.dataloader import goboard


class ScoringTestCase(unittest.TestCase):
    def test_identify_territory(self):
        board = goboard.from_string('''
            ...b..w..
            ...b..w..
            bbbb..w..
            wwwww.www
            wwbbw..w.
            wb.bbwww.
            wbbbb....
            ..b.b....
            ..bbb....
        ''')

        territory = scoring.evaluate_territory(board)

        self.assertEqual(8, territory.num_black_territory)
        self.assertEqual(6, territory.num_white_territory)
        self.assertEqual(20, territory.num_black_stones)
        self.assertEqual(20, territory.num_white_stones)
        self.assertEqual(27, territory.num_dame)

        self.assertIn((0, 0), territory.dame_points)
        self.assertNotIn((8, 0), territory.dame_points)
