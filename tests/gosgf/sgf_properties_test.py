"""Tests for sgf_properties.py."""

import unittest
from textwrap import dedent

from betago.gosgf import sgf_properties


class SgfPropertiesTestCase(unittest.TestCase):
    def test_interpret_simpletext(self):
        def interpret(s, encoding):
            context = sgf_properties._Context(19, encoding)
            return sgf_properties.interpret_simpletext(s, context)
        self.assertEqual(interpret("a\nb\\\\c", "utf-8"), "a b\\c")
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
        self.assertEqual(serialise("ab\\c", "utf-8"), "ab\\\\c")
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
        self.assertEqual(interpret("a\nb\\\\c", "utf-8"), "a\nb\\c")
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
        self.assertEqual(serialise("ab\\c", "utf-8"), "ab\\\\c")
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
        self.assertEqual(serialise_real(1), "1")
        self.assertEqual(serialise_real(-1), "-1")
        self.assertEqual(serialise_real(1.0), "1")
        self.assertEqual(serialise_real(-1.0), "-1")
        self.assertEqual(serialise_real(1.5), "1.5")
        self.assertEqual(serialise_real(-1.5), "-1.5")
        self.assertEqual(serialise_real(0.001), "0.001")
        self.assertEqual(serialise_real(0.0001), "0.0001")
        self.assertEqual(serialise_real(0.00001), "0")
        self.assertEqual(serialise_real(1e15), "1000000000000000")
        self.assertEqual(serialise_real(1e16), "10000000000000000")
        self.assertEqual(serialise_real(1e17), "100000000000000000")
        self.assertEqual(serialise_real(1e18), "1000000000000000000")
        self.assertEqual(serialise_real(-1e18), "-1000000000000000000")
        # 1e400 is inf
        self.assertRaises(ValueError, serialise_real, 1e400)
        # Python 2.5 returns 0
        #self.assertRaises(ValueError, serialise_real, float("NaN"))


    def test_interpret_move(self):
        def interpret_move(s, size):
            context = sgf_properties._Context(size, "UTF-8")
            return sgf_properties.interpret_move(s, context)
        self.assertEqual(interpret_move("aa", 19), (18, 0))
        self.assertEqual(interpret_move("ai", 19), (10, 0))
        self.assertEqual(interpret_move("ba",  9), (8, 1))
        self.assertEqual(interpret_move("tt", 21), (1, 19))
        self.assertIs(interpret_move("tt", 19), None)
        self.assertIs(interpret_move("", 19), None)
        self.assertIs(interpret_move("", 21), None)
        self.assertRaises(ValueError, interpret_move, "Aa", 19)
        self.assertRaises(ValueError, interpret_move, "aA", 19)
        self.assertRaises(ValueError, interpret_move, "aaa", 19)
        self.assertRaises(ValueError, interpret_move, "a", 19)
        self.assertRaises(ValueError, interpret_move, "au", 19)
        self.assertRaises(ValueError, interpret_move, "ua", 19)
        self.assertRaises(ValueError, interpret_move, "a`", 19)
        self.assertRaises(ValueError, interpret_move, "`a", 19)
        self.assertRaises(ValueError, interpret_move, "11", 19)
        self.assertRaises(ValueError, interpret_move, " aa", 19)
        self.assertRaises(ValueError, interpret_move, "aa\x00", 19)
        self.assertRaises(TypeError, interpret_move, None, 19)
        #self.assertRaises(TypeError, interpret_move, ('a', 'a'), 19)

    def test_serialise_move(self):
        def serialise_move(s, size):
            context = sgf_properties._Context(size, "UTF-8")
            return sgf_properties.serialise_move(s, context)
        self.assertEqual(serialise_move((18, 0), 19), "aa")
        self.assertEqual(serialise_move((10, 0), 19), "ai")
        self.assertEqual(serialise_move((8, 1), 19), "bk")
        self.assertEqual(serialise_move((8, 1), 9), "ba")
        self.assertEqual(serialise_move((1, 19), 21), "tt")
        self.assertEqual(serialise_move(None, 19), "tt")
        self.assertEqual(serialise_move(None, 20), "")
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
        self.assertEqual(interpret_point("aa", 19), (18, 0))
        self.assertEqual(interpret_point("ai", 19), (10, 0))
        self.assertEqual(interpret_point("ba",  9), (8, 1))
        self.assertEqual(interpret_point("tt", 21), (1, 19))
        self.assertRaises(ValueError, interpret_point, "tt", 19)
        self.assertRaises(ValueError, interpret_point, "", 19)
        self.assertRaises(ValueError, interpret_point, "", 21)
        self.assertRaises(ValueError, interpret_point, "Aa", 19)
        self.assertRaises(ValueError, interpret_point, "aA", 19)
        self.assertRaises(ValueError, interpret_point, "aaa", 19)
        self.assertRaises(ValueError, interpret_point, "a", 19)
        self.assertRaises(ValueError, interpret_point, "au", 19)
        self.assertRaises(ValueError, interpret_point, "ua", 19)
        self.assertRaises(ValueError, interpret_point, "a`", 19)
        self.assertRaises(ValueError, interpret_point, "`a", 19)
        self.assertRaises(ValueError, interpret_point, "11", 19)
        self.assertRaises(ValueError, interpret_point, " aa", 19)
        self.assertRaises(ValueError, interpret_point, "aa\x00", 19)
        self.assertRaises(TypeError, interpret_point, None, 19)
        #self.assertRaises(TypeError, interpret_point, ('a', 'a'), 19)

    def test_serialise_point(self):
        def serialise_point(s, size):
            context = sgf_properties._Context(size, "UTF-8")
            return sgf_properties.serialise_point(s, context)
        self.assertEqual(serialise_point((18, 0), 19), "aa")
        self.assertEqual(serialise_point((10, 0), 19), "ai")
        self.assertEqual(serialise_point((8, 1), 19), "bk")
        self.assertEqual(serialise_point((8, 1), 9), "ba")
        self.assertEqual(serialise_point((1, 19), 21), "tt")
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
        self.assertEqual(ipl(["aa"], 19),
                         set([(18, 0)]))
        self.assertEqual(ipl(["aa", "ai"], 19),
                         set([(18, 0), (10, 0)]))
        self.assertEqual(ipl(["ab:bc"], 19),
                         set([(16, 0), (16, 1), (17, 0), (17, 1)]))
        self.assertEqual(ipl(["ab:bc", "aa"], 19),
                         set([(18, 0), (16, 0), (16, 1), (17, 0), (17, 1)]))
        # overlap is forbidden by the spec, but we accept it
        self.assertEqual(ipl(["aa", "aa"], 19),
                         set([(18, 0)]))
        self.assertEqual(ipl(["ab:bc", "bb:bc"], 19),
                         set([(16, 0), (16, 1), (17, 0), (17, 1)]))
        # 1x1 rectangles are forbidden by the spec, but we accept them
        self.assertEqual(ipl(["aa", "bb:bb"], 19),
                         set([(18, 0), (17, 1)]))
        # 'backwards' rectangles are forbidden by the spec, and we reject them
        self.assertRaises(ValueError, ipl, ["ab:aa"], 19)
        self.assertRaises(ValueError, ipl, ["ba:aa"], 19)
        self.assertRaises(ValueError, ipl, ["bb:aa"], 19)

        self.assertRaises(ValueError, ipl, ["aa", "tt"], 19)
        self.assertRaises(ValueError, ipl, ["aa", ""], 19)
        self.assertRaises(ValueError, ipl, ["aa:", "aa"], 19)
        self.assertRaises(ValueError, ipl, ["aa:tt", "aa"], 19)
        self.assertRaises(ValueError, ipl, ["tt:aa", "aa"], 19)

    def test_compressed_point_list_spec_example(self):
        # Checks the examples at http://www.red-bean.com/sgf/DD_VW.html
        def sgf_point(move, size):
            row, col = move
            row = size - row - 1
            col_s = "abcdefghijklmnopqrstuvwxy"[col]
            row_s = "abcdefghijklmnopqrstuvwxy"[row]
            return col_s + row_s

        def ipl(l, size):
            context = sgf_properties._Context(size, "UTF-8")
            return sgf_properties.interpret_point_list(l, context)
        self.assertEqual(
            set(sgf_point(move, 9) for move in ipl(["ac:ic"], 9)),
            set(["ac", "bc", "cc", "dc", "ec", "fc", "gc", "hc", "ic"]))
        self.assertEqual(
            set(sgf_point(move, 9) for move in ipl(["ae:ie"], 9)),
            set(["ae", "be", "ce", "de", "ee", "fe", "ge", "he", "ie"]))
        self.assertEqual(
            set(sgf_point(move, 9) for move in ipl(["aa:bi", "ca:ce"], 9)),
            set(["aa", "ab", "ac", "ad", "ae", "af", "ag", "ah", "ai",
                 "bi", "bh", "bg", "bf", "be", "bd", "bc", "bb", "ba",
                 "ca", "cb", "cc", "cd", "ce"]))

    def test_serialise_point_list(self):
        def ipl(l, size):
            context = sgf_properties._Context(size, "UTF-8")
            return sgf_properties.interpret_point_list(l, context)
        def spl(l, size):
            context = sgf_properties._Context(size, "UTF-8")
            return sgf_properties.serialise_point_list(l, context)

        self.assertEqual(spl([(18, 0), (17, 1)], 19), ['aa', 'bb'])
        self.assertEqual(spl([(17, 1), (18, 0)], 19), ['aa', 'bb'])
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

        self.assertEqual(serialise(("foo:bar", "2\n3")), "foo\\:bar:2\n3")
        self.assertEqual(interpret("foo\\:bar:2 3"), ("foo:bar", "2 3"))
        self.assertEqual(interpret("foo bar"), ("foo bar", ""))

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
                         ['ab:cd', 'de:fg'])
        self.assertEqual(interpret(['ab:cd', 'de:fg'], 9),
                         [((7, 0), (5, 2)), ((4, 3), (2, 5))])
        self.assertRaises(ValueError, serialise, [((7, 0), None)], 9)
        self.assertRaises(ValueError, interpret, ['ab:tt', 'de:fg'], 9)

    def test_FG(self):
        def serialise(arg):
            context = sgf_properties._Context(19, "UTF-8")
            return sgf_properties.serialise_FG(arg, context)
        def interpret(arg):
            context = sgf_properties._Context(19, "UTF-8")
            return sgf_properties.interpret_FG(arg, context)
        self.assertEqual(serialise(None), "")
        self.assertEqual(interpret(""), None)
        self.assertEqual(serialise((515, "th]is")), "515:th\\]is")
        self.assertEqual(interpret("515:th\\]is"), (515, "th]is"))

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
            serialise([((6, 0), "lbl"), ((6, 1), "lb]l2")], 9),
            ["ac:lbl", "bc:lb\\]l2"])
        self.assertEqual(
            interpret(["ac:lbl", "bc:lb\\]l2"], 9),
            [((6, 0), "lbl"), ((6, 1), "lb]l2")])
        self.assertRaises(ValueError, serialise, [(None, "lbl")], 9)
        self.assertRaises(ValueError, interpret, [':lbl', 'de:lbl2'], 9)

    def test_presenter_interpret(self):
        p9 = sgf_properties.Presenter(9, "UTF-8")
        p19 = sgf_properties.Presenter(19, "UTF-8")
        self.assertEqual(p9.interpret('KO', [""]), True)
        self.assertEqual(p9.interpret('SZ', ["9"]), 9)
        self.assertRaisesRegexp(ValueError, "multiple values",
                                p9.interpret, 'SZ', ["9", "blah"])
        self.assertEqual(p9.interpret('CR', ["ab", "cd"]), set([(5, 2), (7, 0)]))
        self.assertRaises(ValueError, p9.interpret, 'SZ', [])
        self.assertRaises(ValueError, p9.interpret, 'CR', [])
        self.assertEqual(p9.interpret('DD', [""]), set())
        # all lists are treated like elists
        self.assertEqual(p9.interpret('CR', [""]), set())

    def test_presenter_serialise(self):
        p9 = sgf_properties.Presenter(9, "UTF-8")
        p19 = sgf_properties.Presenter(19, "UTF-8")

        self.assertEqual(p9.serialise('KO', True), [""])
        self.assertEqual(p9.serialise('SZ', 9), ["9"])
        self.assertEqual(p9.serialise('KM', 3.5), ["3.5"])
        self.assertEqual(p9.serialise('C', "foo\\:b]ar\n"), ["foo\\\\:b\\]ar\n"])
        self.assertEqual(p19.serialise('B', (1, 2)), ["cr"])
        self.assertEqual(p9.serialise('B', None), ["tt"])
        self.assertEqual(p19.serialise('AW', set([(17, 1), (18, 0)])),["aa", "bb"])
        self.assertEqual(p9.serialise('DD', [(1, 2), (3, 4)]), ["ch", "ef"])
        self.assertEqual(p9.serialise('DD', []), [""])
        self.assertRaisesRegexp(ValueError, "empty list", p9.serialise, 'CR', [])
        self.assertEqual(p9.serialise('AP', ("na:me", "2.3")), ["na\\:me:2.3"])
        self.assertEqual(p9.serialise('FG', (515, "th]is")), ["515:th\\]is"])
        self.assertEqual(p9.serialise('XX', "foo\\bar"), ["foo\\\\bar"])

        self.assertRaises(ValueError, p9.serialise, 'B', (1, 9))

    def test_presenter_private_properties(self):
        p9 = sgf_properties.Presenter(9, "UTF-8")
        self.assertEqual(p9.serialise('XX', "9"), ["9"])
        self.assertEqual(p9.interpret('XX', ["9"]), "9")
        p9.set_private_property_type(p9.get_property_type("SZ"))
        self.assertEqual(p9.serialise('XX', 9), ["9"])
        self.assertEqual(p9.interpret('XX', ["9"]), 9)
        p9.set_private_property_type(None)
        self.assertRaisesRegexp(ValueError, "unknown property",
                                p9.serialise, 'XX', "foo\\bar")
        self.assertRaisesRegexp(ValueError, "unknown property",
                                p9.interpret, 'XX', ["asd"])
