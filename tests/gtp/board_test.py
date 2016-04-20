import unittest

from betago.gtp.board import coords_to_gtp_position, gtp_position_to_coords


class GTPCoordinateTest(unittest.TestCase):
    def test_coords_to_gtp_position(self):
        self.assertEqual('A1', coords_to_gtp_position((0, 0)))
        self.assertEqual('J3', coords_to_gtp_position((2, 8)))
        self.assertEqual('B15', coords_to_gtp_position((14, 1)))

    def test_gtp_position_to_coords(self):
        self.assertEqual((0, 0), gtp_position_to_coords('A1'))
        self.assertEqual((2, 8), gtp_position_to_coords('J3'))
        self.assertEqual((14, 1), gtp_position_to_coords('B15'))
