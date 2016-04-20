import unittest

from betago.gtp import command, response


class ResponseTestCase(unittest.TestCase):
    def setUp(self):
        self.cmd = command.Command(None, 'genmove', ('black',))
        self.cmd_with_sequence = command.Command(99, 'genmove', ('black',))

    def test_serialize(self):
        resp = response.success('D4')

        self.assertEqual('= D4\n\n', response.serialize(self.cmd, resp))

    def test_serialize_error(self):
        resp = response.error('fail!')

        self.assertEqual('? fail!\n\n', response.serialize(self.cmd, resp))

    def test_serialize_with_sequence(self):
        resp = response.success('D4')

        self.assertEqual('=99 D4\n\n', response.serialize(self.cmd_with_sequence, resp))

    def test_serialize_error_with_sequence(self):
        resp = response.error('fail!')

        self.assertEqual('?99 fail!\n\n', response.serialize(self.cmd_with_sequence, resp))
