import unittest

from betago.gtp import command


class CommandTestCase(unittest.TestCase):
    def test_parse(self):
        command_string = 'play white D4'
        expected = command.Command(
            sequence=None,
            name='play',
            args=('white', 'D4'),
        )
        self.assertEqual(expected, command.parse(command_string))

    def test_parse_with_sequence_number(self):
        command_string = '999 play white D4'
        expected = command.Command(
            sequence=999,
            name='play',
            args=('white', 'D4'),
        )
        self.assertEqual(expected, command.parse(command_string))
