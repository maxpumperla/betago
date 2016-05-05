"""Tests for sgf_properties.py."""

import unittest
from textwrap import dedent

from betago.gosgf import sgf_properties


class SgfPropertiesTestCase(unittest.TestCase):
    def test_interpret_simpletext(self):
        def interpret(s, encoding):
            context = sgf_properties._Context(19, encoding)
            return sgf_properties.interpret_simpletext(s, context)
        self.assertEqual(interpret(b"a\nb\\\\c", "utf-8"), b"a b\\c")
        u = u"test \N{POUND SIGN}"
        self.assertEqual(interpret(u.encode("utf-8"), "UTF-8"),
                         u.encode("utf-8"))
        self.assertEqual(interpret(u.encode("iso-8859-1"), "ISO-8859-1"),
                         u.encode("utf-8"))
        self.assertRaises(UnicodeDecodeError, interpret,
                          u.encode("iso-8859-1"), "UTF-8")
        self.assertRaises(UnicodeDecodeError, interpret, u.encode("utf-8"), "ASCII")

    def test_serialise_simpletext(self):
        def serialise(s, encoding):
            context = sgf_properties._Context(19, encoding)
            return sgf_properties.serialise_simpletext(s, context)
        self.assertEqual(serialise(b"ab\\c", "utf-8"), b"ab\\\\c")
        u = u"test \N{POUND SIGN}"
        self.assertEqual(serialise(u.encode("utf-8"), "UTF-8"),
                         u.encode("utf-8"))
        self.assertEqual(serialise(u.encode("utf-8"), "ISO-8859-1"),
                         u.encode("iso-8859-1"))
        self.assertRaises(UnicodeEncodeError, serialise,
                          u"\N{EN DASH}".encode("utf-8"), "ISO-8859-1")

    def test_interpret_text(self):
        def interpret(s, encoding):
            context = sgf_properties._Context(19, encoding)
            return sgf_properties.interpret_text(s, context)
        self.assertEqual(interpret(b"a\nb\\\\c", "utf-8"), b"a\nb\\c")
        u = u"test \N{POUND SIGN}"
        self.assertEqual(interpret(u.encode("utf-8"), "UTF-8"),
                         u.encode("utf-8"))
        self.assertEqual(interpret(u.encode("iso-8859-1"), "ISO-8859-1"),
                         u.encode("utf-8"))
        self.assertRaises(UnicodeDecodeError, interpret,
                          u.encode("iso-8859-1"), "UTF-8")
        self.assertRaises(UnicodeDecodeError, interpret, u.encode("utf-8"), "ASCII")

    def test_serialise_text(self):
        def serialise(s, encoding):
            context = sgf_properties._Context(19, encoding)
            return sgf_properties.serialise_text(s, context)
        self.assertEqual(serialise(b"ab\\c", "utf-8"), b"ab\\\\c")
        u = u"test \N{POUND SIGN}"
        self.assertEqual(serialise(u.encode("utf-8"), "UTF-8"),
                         u.encode("utf-8"))
        self.assertEqual(serialise(u.encode("utf-8"), "ISO-8859-1"),
                         u.encode("iso-8859-1"))
        self.assertRaises(UnicodeEncodeError, serialise,
                          u"\N{EN DASH}".encode("utf-8"), "ISO-8859-1")

    def test_interpret_number(self):
        interpret_number = sgf_properties.interpret_number
        self.assertEqual(interpret_number("1"), 1)
        self.assertIs(type(interpret_number("1")), int)
        self.assertEqual(interpret_number("0"), 0)
        self.assertEqual(interpret_number("-1"), -1)
        self.assertEqual(interpret_number("+1"), 1)
        self.assertRaises(ValueError, interpret_number, "1.5")
        self.assertRaises(ValueError, interpret_number, "0xaf")
        self.assertRaises(TypeError, interpret_number, 1)

    def test_interpret_real(self):
        interpret_real = sgf_properties.interpret_real
        self.assertEqual(interpret_real("1"), 1.0)
        self.assertIs(type(interpret_real("1")), float)
        self.assertEqual(interpret_real("0"), 0.0)
        self.assertEqual(interpret_real("1.0"), 1.0)
        self.assertEqual(interpret_real("1.5"), 1.5)
        self.assertEqual(interpret_real("-1.5"), -1.5)
        self.assertEqual(interpret_real("+0.5"), 0.5)
        self.assertRaises(ValueError, interpret_real, "+")
        self.assertRaises(ValueError, interpret_real, "0xaf")
        self.assertRaises(ValueError, interpret_real, "inf")
        self.assertRaises(ValueError, interpret_real, "-inf")
        self.assertRaises(ValueError, interpret_real, "NaN")
        self.assertRaises(ValueError, interpret_real, "1e400")
        #self.assertRaises(TypeError, interpret_real, 1.0)

    def test_serialise_real(self):
        serialise_real = sgf_properties.serialise_real
        self.assertEqual(serialise_real(1), b"1")
        self.assertEqual(serialise_real(-1), b"-1")
        self.assertEqual(serialise_real(1.0), b"1")
        self.assertEqual(serialise_real(-1.0), b"-1")
        self.assertEqual(serialise_real(1.5), b"1.5")
        self.assertEqual(serialise_real(-1.5), b"-1.5")
        self.assertEqual(serialise_real(0.001), b"0.001")
        self.assertEqual(serialise_real(0.0001), b"0.0001")
        self.assertEqual(serialise_real(0.00001), b"0")
        self.assertEqual(serialise_real(1e15), b"1000000000000000")
        self.assertEqual(serialise_real(1e16), b"10000000000000000")
        self.assertEqual(serialise_real(1e17), b"100000000000000000")
        self.assertEqual(serialise_real(1e18), b"1000000000000000000")
        self.assertEqual(serialise_real(-1e18), b"-1000000000000000000")
        # 1e400 is inf
        self.assertRaises(ValueError, serialise_real, 1e400)
        # Python 2.5 returns 0
        #self.assertRaises(ValueError, serialise_real, float("NaN"))


    def test_interpret_move(self):
        def interpret_move(s, size):
            context = sgf_properties._Context(size, "UTF-8")
            return sgf_properties.interpret_move(s, context)
        self.assertEqual(interpret_move(b"aa", 19), (18, 0))
        self.assertEqual(interpret_move(b"ai", 19), (10, 0))
        self.assertEqual(interpret_move(b"ba",  9), (8, 1))
        self.assertEqual(interpret_move(b"tt", 21), (1, 19))
        self.assertIs(interpret_move(b"tt", 19), None)
        self.assertIs(interpret_move(b"", 19), None)
        self.assertIs(interpret_move(b"", 21), None)
        self.assertRaises(ValueError, interpret_move, b"Aa", 19)
        self.assertRaises(ValueError, interpret_move, b"aA", 19)
        self.assertRaises(ValueError, interpret_move, b"aaa", 19)
        self.assertRaises(ValueError, interpret_move, b"a", 19)
        self.assertRaises(ValueError, interpret_move, b"au", 19)
        self.assertRaises(ValueError, interpret_move, b"ua", 19)
        self.assertRaises(ValueError, interpret_move, b"a`", 19)
        self.assertRaises(ValueError, interpret_move, b"`a", 19)
        self.assertRaises(ValueError, interpret_move, b"11", 19)
        self.assertRaises(ValueError, interpret_move, b" aa", 19)
        self.assertRaises(ValueError, interpret_move, b"aa\x00", 19)
        self.assertRaises(TypeError, interpret_move, None, 19)
        #self.assertRaises(TypeError, interpret_move, ('a', 'a'), 19)

    def test_serialise_move(self):
        def serialise_move(s, size):
            context = sgf_properties._Context(size, "UTF-8")
            return sgf_properties.serialise_move(s, context)
        self.assertEqual(serialise_move((18, 0), 19), b"aa")
        self.assertEqual(serialise_move((10, 0), 19), b"ai")
        self.assertEqual(serialise_move((8, 1), 19), b"bk")
        self.assertEqual(serialise_move((8, 1), 9), b"ba")
        self.assertEqual(serialise_move((1, 19), 21), b"tt")
        self.assertEqual(serialise_move(None, 19), b"tt")
        self.assertEqual(serialise_move(None, 20), b"")
        self.assertRaises(ValueError, serialise_move, (3, 3), 0)
        self.assertRaises(ValueError, serialise_move, (3, 3), 27)
        self.assertRaises(ValueError, serialise_move, (9, 0), 9)
        self.assertRaises(ValueError, serialise_move, (-1, 0), 9)
        self.assertRaises(ValueError, serialise_move, (0, 9), 9)
        self.assertRaises(ValueError, serialise_move, (0, -1), 9)
        self.assertRaises(TypeError, serialise_move, (1, 1.5), 9)

    def test_interpret_point(self):
        def interpret_point(s, size):
            context = sgf_properties._Context(size, "UTF-8")
            return sgf_properties.interpret_point(s, context)
        self.assertEqual(interpret_point(b"aa", 19), (18, 0))
        self.assertEqual(interpret_point(b"ai", 19), (10, 0))
        self.assertEqual(interpret_point(b"ba",  9), (8, 1))
        self.assertEqual(interpret_point(b"tt", 21), (1, 19))
        self.assertRaises(ValueError, interpret_point, b"tt", 19)
        self.assertRaises(ValueError, interpret_point, b"", 19)
        self.assertRaises(ValueError, interpret_point, b"", 21)
        self.assertRaises(ValueError, interpret_point, b"Aa", 19)
        self.assertRaises(ValueError, interpret_point, b"aA", 19)
        self.assertRaises(ValueError, interpret_point, b"aaa", 19)
        self.assertRaises(ValueError, interpret_point, b"a", 19)
        self.assertRaises(ValueError, interpret_point, b"au", 19)
        self.assertRaises(ValueError, interpret_point, b"ua", 19)
        self.assertRaises(ValueError, interpret_point, b"a`", 19)
        self.assertRaises(ValueError, interpret_point, b"`a", 19)
        self.assertRaises(ValueError, interpret_point, b"11", 19)
        self.assertRaises(ValueError, interpret_point, b" aa", 19)
        self.assertRaises(ValueError, interpret_point, b"aa\x00", 19)
        self.assertRaises(TypeError, interpret_point, None, 19)
        #self.assertRaises(TypeError, interpret_point, ('a', 'a'), 19)

    def test_serialise_point(self):
        def serialise_point(s, size):
            context = sgf_properties._Context(size, "UTF-8")
            return sgf_properties.serialise_point(s, context)
        self.assertEqual(serialise_point((18, 0), 19), b"aa")
        self.assertEqual(serialise_point((10, 0), 19), b"ai")
        self.assertEqual(serialise_point((8, 1), 19), b"bk")
        self.assertEqual(serialise_point((8, 1), 9), b"ba")
        self.assertEqual(serialise_point((1, 19), 21), b"tt")
        self.assertRaises(ValueError, serialise_point, None, 19)
        self.assertRaises(ValueError, serialise_point, None, 20)
        self.assertRaises(ValueError, serialise_point, (3, 3), 0)
        self.assertRaises(ValueError, serialise_point, (3, 3), 27)
        self.assertRaises(ValueError, serialise_point, (9, 0), 9)
        self.assertRaises(ValueError, serialise_point, (-1, 0), 9)
        self.assertRaises(ValueError, serialise_point, (0, 9), 9)
        self.assertRaises(ValueError, serialise_point, (0, -1), 9)
        self.assertRaises(TypeError, serialise_point, (1, 1.5), 9)


    def test_interpret_point_list(self):
        def ipl(l, size):
            context = sgf_properties._Context(size, "UTF-8")
            return sgf_properties.interpret_point_list(l, context)
        self.assertEqual(ipl([], 19),
                         set())
        self.assertEqual(ipl([b"aa"], 19),
                         set([(18, 0)]))
        self.assertEqual(ipl([b"aa", b"ai"], 19),
                         set([(18, 0), (10, 0)]))
        self.assertEqual(ipl([b"ab:bc"], 19),
                         set([(16, 0), (16, 1), (17, 0), (17, 1)]))
        self.assertEqual(ipl([b"ab:bc", b"aa"], 19),
                         set([(18, 0), (16, 0), (16, 1), (17, 0), (17, 1)]))
        # overlap is forbidden by the spec, but we accept it
        self.assertEqual(ipl([b"aa", b"aa"], 19),
                         set([(18, 0)]))
        self.assertEqual(ipl([b"ab:bc", b"bb:bc"], 19),
                         set([(16, 0), (16, 1), (17, 0), (17, 1)]))
        # 1x1 rectangles are forbidden by the spec, but we accept them
        self.assertEqual(ipl([b"aa", b"bb:bb"], 19),
                         set([(18, 0), (17, 1)]))
        # 'backwards' rectangles are forbidden by the spec, and we reject them
        self.assertRaises(ValueError, ipl, [b"ab:aa"], 19)
        self.assertRaises(ValueError, ipl, [b"ba:aa"], 19)
        self.assertRaises(ValueError, ipl, [b"bb:aa"], 19)

        self.assertRaises(ValueError, ipl, [b"aa", b"tt"], 19)
        self.assertRaises(ValueError, ipl, [b"aa", b""], 19)
        self.assertRaises(ValueError, ipl, [b"aa:", b"aa"], 19)
        self.assertRaises(ValueError, ipl, [b"aa:tt", b"aa"], 19)
        self.assertRaises(ValueError, ipl, [b"tt:aa", b"aa"], 19)

    def test_compressed_point_list_spec_example(self):
        # Checks the examples at http://www.red-bean.com/sgf/DD_VW.html
        def sgf_point(move, size):
            row, col = move
            row = size - row - 1
            col_s = "abcdefghijklmnopqrstuvwxy"[col].encode('ascii')
            row_s = "abcdefghijklmnopqrstuvwxy"[row].encode('ascii')
            return col_s + row_s

        def ipl(l, size):
            context = sgf_properties._Context(size, "UTF-8")
            return sgf_properties.interpret_point_list(l, context)
        self.assertEqual(
            set(sgf_point(move, 9) for move in ipl([b"ac:ic"], 9)),
            set([b"ac", b"bc", b"cc", b"dc", b"ec", b"fc", b"gc", b"hc", b"ic"]))
        self.assertEqual(
            set(sgf_point(move, 9) for move in ipl([b"ae:ie"], 9)),
            set([b"ae", b"be", b"ce", b"de", b"ee", b"fe", b"ge", b"he", b"ie"]))
        self.assertEqual(
            set(sgf_point(move, 9) for move in ipl([b"aa:bi", b"ca:ce"], 9)),
            set([b"aa", b"ab", b"ac", b"ad", b"ae", b"af", b"ag", b"ah", b"ai",
                 b"bi", b"bh", b"bg", b"bf", b"be", b"bd", b"bc", b"bb", b"ba",
                 b"ca", b"cb", b"cc", b"cd", b"ce"]))

    def test_serialise_point_list(self):
        def ipl(l, size):
            context = sgf_properties._Context(size, "UTF-8")
            return sgf_properties.interpret_point_list(l, context)
        def spl(l, size):
            context = sgf_properties._Context(size, "UTF-8")
            return sgf_properties.serialise_point_list(l, context)

        self.assertEqual(spl([(18, 0), (17, 1)], 19), [b'aa', b'bb'])
        self.assertEqual(spl([(17, 1), (18, 0)], 19), [b'aa', b'bb'])
        self.assertEqual(spl([], 9), [])
        self.assertEqual(ipl(spl([(1,2), (3,4), (4,5)], 19), 19),
                         set([(1,2), (3,4), (4,5)]))
        self.assertRaises(ValueError, spl, [(18, 0), None], 19)

    def test_AP(self):
        def serialise(arg):
            context = sgf_properties._Context(19, "UTF-8")
            return sgf_properties.serialise_AP(arg, context)
        def interpret(arg):
            context = sgf_properties._Context(19, "UTF-8")
            return sgf_properties.interpret_AP(arg, context)

        self.assertEqual(serialise((b"foo:bar", b"2\n3")), b"foo\\:bar:2\n3")
        self.assertEqual(interpret(b"foo\\:bar:2 3"), (b"foo:bar", b"2 3"))
        self.assertEqual(interpret(b"foo bar"), (b"foo bar", b""))

    def test_ARLN(self):
        def serialise(arg, size):
            context = sgf_properties._Context(size, "UTF-8")
            return sgf_properties.serialise_ARLN_list(arg, context)
        def interpret(arg, size):
            context = sgf_properties._Context(size, "UTF-8")
            return sgf_properties.interpret_ARLN_list(arg, context)

        self.assertEqual(serialise([], 19), [])
        self.assertEqual(interpret([], 19), [])
        self.assertEqual(serialise([((7, 0), (5, 2)), ((4, 3), (2, 5))], 9),
                         [b'ab:cd', b'de:fg'])
        self.assertEqual(interpret([b'ab:cd', b'de:fg'], 9),
                         [((7, 0), (5, 2)), ((4, 3), (2, 5))])
        self.assertRaises(ValueError, serialise, [((7, 0), None)], 9)
        self.assertRaises(ValueError, interpret, [b'ab:tt', b'de:fg'], 9)

    def test_FG(self):
        def serialise(arg):
            context = sgf_properties._Context(19, "UTF-8")
            return sgf_properties.serialise_FG(arg, context)
        def interpret(arg):
            context = sgf_properties._Context(19, "UTF-8")
            return sgf_properties.interpret_FG(arg, context)
        self.assertEqual(serialise(None), b"")
        self.assertEqual(interpret(b""), None)
        self.assertEqual(serialise((515, b"th]is")), b"515:th\\]is")
        self.assertEqual(interpret(b"515:th\\]is"), (515, b"th]is"))

    def test_LB(self):
        def serialise(arg, size):
            context = sgf_properties._Context(size, "UTF-8")
            return sgf_properties.serialise_LB_list(arg, context)
        def interpret(arg, size):
            context = sgf_properties._Context(size, "UTF-8")
            return sgf_properties.interpret_LB_list(arg, context)
        self.assertEqual(serialise([], 19), [])
        self.assertEqual(interpret([], 19), [])
        self.assertEqual(
            serialise([((6, 0), b"lbl"), ((6, 1), b"lb]l2")], 9),
            [b"ac:lbl", b"bc:lb\\]l2"])
        self.assertEqual(
            interpret([b"ac:lbl", b"bc:lb\\]l2"], 9),
            [((6, 0), b"lbl"), ((6, 1), b"lb]l2")])
        self.assertRaises(ValueError, serialise, [(None, b"lbl")], 9)
        self.assertRaises(ValueError, interpret, [b':lbl', b'de:lbl2'], 9)

    def test_presenter_interpret(self):
        p9 = sgf_properties.Presenter(9, "UTF-8")
        p19 = sgf_properties.Presenter(19, "UTF-8")
        self.assertEqual(p9.interpret(b'KO', [b""]), True)
        self.assertEqual(p9.interpret(b'SZ', [b"9"]), 9)
        self.assertRaisesRegexp(ValueError, "multiple values",
                                p9.interpret, b'SZ', [b"9", b"blah"])
        self.assertEqual(p9.interpret(b'CR', [b"ab", b"cd"]), set([(5, 2), (7, 0)]))
        self.assertRaises(ValueError, p9.interpret, b'SZ', [])
        self.assertRaises(ValueError, p9.interpret, b'CR', [])
        self.assertEqual(p9.interpret(b'DD', [b""]), set())
        # all lists are treated like elists
        self.assertEqual(p9.interpret(b'CR', [b""]), set())

    def test_presenter_serialise(self):
        p9 = sgf_properties.Presenter(9, "UTF-8")
        p19 = sgf_properties.Presenter(19, "UTF-8")

        self.assertEqual(p9.serialise(b'KO', True), [b""])
        self.assertEqual(p9.serialise(b'SZ', 9), [b"9"])
        self.assertEqual(p9.serialise(b'KM', 3.5), [b"3.5"])
        self.assertEqual(p9.serialise(b'C', b"foo\\:b]ar\n"), [b"foo\\\\:b\\]ar\n"])
        self.assertEqual(p19.serialise(b'B', (1, 2)), [b"cr"])
        self.assertEqual(p9.serialise(b'B', None), [b"tt"])
        self.assertEqual(p19.serialise(b'AW', set([(17, 1), (18, 0)])),[b"aa", b"bb"])
        self.assertEqual(p9.serialise(b'DD', [(1, 2), (3, 4)]), [b"ch", b"ef"])
        self.assertEqual(p9.serialise(b'DD', []), [b""])
        self.assertRaisesRegexp(ValueError, "empty list", p9.serialise, b'CR', [])
        self.assertEqual(p9.serialise(b'AP', (b"na:me", b"2.3")), [b"na\\:me:2.3"])
        self.assertEqual(p9.serialise(b'FG', (515, b"th]is")), [b"515:th\\]is"])
        self.assertEqual(p9.serialise(b'XX', b"foo\\bar"), [b"foo\\\\bar"])

        self.assertRaises(ValueError, p9.serialise, b'B', (1, 9))

    def test_presenter_private_properties(self):
        p9 = sgf_properties.Presenter(9, "UTF-8")
        self.assertEqual(p9.serialise(b'XX', b"9"), [b"9"])
        self.assertEqual(p9.interpret(b'XX', [b"9"]), b"9")
        p9.set_private_property_type(p9.get_property_type(b"SZ"))
        self.assertEqual(p9.serialise(b'XX', 9), [b"9"])
        self.assertEqual(p9.interpret(b'XX', [b"9"]), 9)
        p9.set_private_property_type(None)
        self.assertRaisesRegexp(ValueError, "unknown property",
                                p9.serialise, b'XX', b"foo\\bar")
        self.assertRaisesRegexp(ValueError, "unknown property",
                                p9.interpret, b'XX', [b"asd"])
