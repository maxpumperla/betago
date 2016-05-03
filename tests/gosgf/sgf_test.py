# -*- coding: utf-8 -*-
"""Tests for sgf.py."""

import unittest
from textwrap import dedent

from betago import gosgf

SAMPLE_SGF = """\
(;AP[testsuite:0]CA[utf-8]DT[2009-06-06]FF[4]GM[1]KM[7.5]PB[Black engine]
PL[B]PW[White engine]RE[W+R]SZ[9]AB[ai][bh][ee]AW[fc][gc];B[dg];W[ef]C[comment
on two lines];B[];W[tt]C[Final comment])
"""

SAMPLE_SGF_VAR = """\
(;AP[testsuite:0]CA[utf-8]DT[2009-06-06]FF[4]GM[1]KM[7.5]PB[Black engine]
PL[B]RE[W+R]SZ[9]AB[ai][bh][ee]AW[fd][gc]VW[]
;B[dg]
;W[ef]C[comment
on two lines]
;B[]
;C[Nonfinal comment]VW[aa:bb]
(;B[ia];W[ib];B[ic])
(;B[ib];W[ic]
  (;B[id])
  (;B[ie])
))
"""


class SgfTestCase(unittest.TestCase):
    def test_new_sgf_game(self):
        g1 = gosgf.Sgf_game(9)
        self.assertEqual(g1.get_size(), 9)
        root = g1.get_root()
        self.assertEqual(root.get_raw('FF'), '4')
        self.assertEqual(root.get_raw('GM'), '1')
        self.assertEqual(root.get_raw('SZ'), '9')
        self.assertEqual(root.get_raw_property_map(), {
            'FF': ['4'],
            'GM': ['1'],
            'SZ': ['9'],
            'CA': ['UTF-8'],
            });
        self.assertEqual(list(root), [])
        self.assertEqual(root.parent, None)
        self.assertIs(root.owner, g1)

    def test_sgf_game_from_coarse_game_tree(self):
        class Namespace(object):
            pass
        coarse_game = Namespace()
        coarse_game.sequence = [{'SZ' : ["9"]}, {'B' : ["aa"]}]
        coarse_game.children = []
        g1 = gosgf.Sgf_game.from_coarse_game_tree(coarse_game)
        self.assertEqual(g1.get_size(), 9)
        root = g1.get_root()
        self.assertIs(root.get_raw_property_map(), coarse_game.sequence[0])
        self.assertEqual(root.parent, None)
        self.assertIs(root.owner, g1)
        self.assertEqual(len(root), 1)

        coarse_game2 = Namespace()
        coarse_game2.sequence = [{'SZ' : ["0"]}, {'B' : ["aa"]}]
        coarse_game2.children = []
        self.assertRaisesRegexp(ValueError, "size out of range: 0",
                                gosgf.Sgf_game.from_coarse_game_tree, coarse_game2)

    def test_sgf_game_from_string(self):
        g1 = gosgf.Sgf_game.from_string("(;)")
        self.assertEqual(g1.get_size(), 19)
        self.assertRaisesRegexp(ValueError, "unexpected end of SGF data",
                                gosgf.Sgf_game.from_string, "(;SZ[9]")
        g2 = gosgf.Sgf_game.from_string("(;SZ[9])")
        self.assertEqual(g2.get_size(), 9)
        self.assertRaisesRegexp(ValueError, "bad SZ property: a",
                                gosgf.Sgf_game.from_string, "(;SZ[a])")
        self.assertRaisesRegexp(ValueError, "size out of range: 27",
                              gosgf.Sgf_game.from_string, "(;SZ[27])")
        self.assertRaisesRegexp(ValueError, "unknown encoding: $",
                              gosgf.Sgf_game.from_string, "(;CA[])")
    
    def test_node(self):
        sgf_game = gosgf.Sgf_game.from_string(
            r"(;KM[6.5]C[sample\: comment]AB[ai][bh][ee]AE[];B[dg])")
        node0 = sgf_game.get_root()
        node1 = list(sgf_game.main_sequence_iter())[1]
        self.assertEqual(node0.get_size(), 19)
        self.assertEqual(node0.get_encoding(), "ISO-8859-1")
        self.assertIs(node0.has_property('KM'), True)
        self.assertIs(node0.has_property('XX'), False)
        self.assertIs(node1.has_property('KM'), False)
        self.assertEqual(set(node0.properties()), set(["KM", "C", "AB", "AE"]))
        self.assertEqual(set(node1.properties()), set(["B"]))
        self.assertEqual(node0.get_raw('C'), r"sample\: comment")
        self.assertEqual(node0.get_raw('AB'), "ai")
        self.assertEqual(node0.get_raw('AE'), "")
        self.assertRaises(KeyError, node0.get_raw, 'XX')
        self.assertEqual(node0.get_raw_list('KM'), ['6.5'])
        self.assertEqual(node0.get_raw_list('AB'), ['ai', 'bh', 'ee'])
        self.assertEqual(node0.get_raw_list('AE'), [''])
        self.assertRaises(KeyError, node0.get_raw_list, 'XX')
        self.assertRaises(KeyError, node0.get_raw, 'XX')
    
    def test_property_combination(self):
        sgf_game = gosgf.Sgf_game.from_string("(;XX[1]YY[2]XX[3]YY[4])")
        node0 = sgf_game.get_root()
        self.assertEqual(node0.get_raw_list("XX"), ["1", "3"])
        self.assertEqual(node0.get_raw_list("YY"), ["2", "4"])
    
    def test_node_get(self):
        sgf_game = gosgf.Sgf_game.from_string(dedent(r"""
        (;AP[testsuite:0]CA[utf-8]DT[2009-06-06]FF[4]GM[1]KM[7.5]PB[Black engine]
        PL[B]PW[White engine][xs]RE[W+R]SZ[9]AB[ai][bh][ee]AW[fd][gc]AE[]BM[2]VW[]
        EV[Test
        event]
        C[123:\)
        abc]
        YY[none
        sense]
        ;B[dg]KO[]AR[ab:cd][de:fg]FG[515:first move]
        LB[ac:lbl][bc:lbl2])
        """))
        root = sgf_game.get_root()
        node1 = list(sgf_game.main_sequence_iter())[1]
        self.assertRaises(KeyError, root.get, 'XX')
        self.assertEqual(root.get('C'), "123:)\nabc")          # Text
        self.assertEqual(root.get('EV'), "Test event")         # Simpletext
        self.assertEqual(root.get('BM'), 2)                    # Double
        self.assertEqual(root.get('YY'), "none\nsense")        # unknown (Text)
        self.assertIs(node1.get('KO'), True)                   # None
        self.assertEqual(root.get('KM'), 7.5)                  # Real
        self.assertEqual(root.get('GM'), 1)                    # Number
        self.assertEqual(root.get('PL'), 'b')                  # Color
        self.assertEqual(node1.get('B'), (2, 3))               # Point
        self.assertEqual(root.get('AB'),
                       set([(0, 0), (1, 1), (4, 4)]))        # List of Point
        self.assertEqual(root.get('VW'), set())                # Empty elist
        self.assertEqual(root.get('AP'), ("testsuite", "0"))   # Application
        self.assertEqual(node1.get('AR'),
                       [((7, 0), (5, 2)), ((4, 3), (2, 5))]) # Arrow
        self.assertEqual(node1.get('FG'), (515, "first move")) # Figure
        self.assertEqual(node1.get('LB'),
                       [((6, 0), "lbl"), ((6, 1), "lbl2")])  # Label
        # Check we (leniently) treat lists like elists on read
        self.assertEqual(root.get('AE'), set())
        self.assertRaisesRegexp(ValueError, "multiple values", root.get, 'PW')
    
    def test_text_values(self):
        def check(s):
            sgf_game = gosgf.Sgf_game.from_string(s)
            return sgf_game.get_root().get("C")
        # Round-trip check of Text values through tokeniser, parser, and
        # text_value().
        self.assertEqual(check(r"(;C[abc]KO[])"), r"abc")
        self.assertEqual(check(r"(;C[a\\bc]KO[])"), r"a\bc")
        self.assertEqual(check(r"(;C[a\\bc\]KO[])"), r"a\bc]KO[")
        self.assertEqual(check(r"(;C[abc\\]KO[])"), r"abc" + "\\")
        self.assertEqual(check(r"(;C[abc\\\]KO[])"), r"abc\]KO[")
        self.assertEqual(check(r"(;C[abc\\\\]KO[])"), r"abc" + "\\\\")
        self.assertEqual(check(r"(;C[abc\\\\\]KO[])"), r"abc\\]KO[")
        self.assertEqual(check(r"(;C[xxx :\) yyy]KO[])"), r"xxx :) yyy")
        self.assertEqual(check("(;C[ab\\\nc])"), "abc")
        self.assertEqual(check("(;C[ab\nc])"), "ab\nc")



    def test_node_string(self):
        sgf_game = gosgf.Sgf_game.from_string(SAMPLE_SGF)
        node = sgf_game.get_root()
        self.assertMultiLineEqual(str(node), dedent("""\
        AB[ai][bh][ee]
        AP[testsuite:0]
        AW[fc][gc]
        CA[utf-8]
        DT[2009-06-06]
        FF[4]
        GM[1]
        KM[7.5]
        PB[Black engine]
        PL[B]
        PW[White engine]
        RE[W+R]
        SZ[9]
        """))

    def test_node_get_move(self):
        sgf_game = gosgf.Sgf_game.from_string(SAMPLE_SGF)
        nodes = list(sgf_game.main_sequence_iter())
        self.assertEqual(nodes[0].get_move(), (None, None))
        self.assertEqual(nodes[1].get_move(), ('b', (2, 3)))
        self.assertEqual(nodes[2].get_move(), ('w', (3, 4)))
        self.assertEqual(nodes[3].get_move(), ('b', None))
        self.assertEqual(nodes[4].get_move(), ('w', None))

    def test_node_get_setup_stones(self):
        sgf_game = gosgf.Sgf_game.from_string(
            r"(;KM[6.5]SZ[9]C[sample\: comment]AB[ai][bh][ee]AE[bb];B[dg])")
        node0 = sgf_game.get_root()
        node1 = list(sgf_game.main_sequence_iter())[1]
        self.assertIs(node0.has_setup_stones(), True)
        self.assertIs(node1.has_setup_stones(), False)
        self.assertEqual(node0.get_setup_stones(),
                       (set([(0, 0), (1, 1), (4, 4)]), set(), set([(7, 1)])))
        self.assertEqual(node1.get_setup_stones(),
                       (set(), set(), set()))

    def test_sgf_game(self):
        sgf_game = gosgf.Sgf_game.from_string(SAMPLE_SGF_VAR)
        nodes = list(sgf_game.main_sequence_iter())
        self.assertEqual(sgf_game.get_size(), 9)
        self.assertEqual(sgf_game.get_komi(), 7.5)
        self.assertIs(sgf_game.get_handicap(), None)
        self.assertEqual(sgf_game.get_player_name('b'), "Black engine")
        self.assertIs(sgf_game.get_player_name('w'), None)
        self.assertEqual(sgf_game.get_winner(), 'w')
        self.assertEqual(nodes[2].get('C'), "comment\non two lines")
        self.assertEqual(nodes[4].get('C'), "Nonfinal comment")

        g2 = gosgf.Sgf_game.from_string("(;)")
        self.assertEqual(g2.get_size(), 19)
        self.assertEqual(g2.get_komi(), 0.0)
        self.assertIs(g2.get_handicap(), None)
        self.assertIs(g2.get_player_name('b'), None)
        self.assertIs(g2.get_player_name('w'), None)
        self.assertEqual(g2.get_winner(), None)

    def test_tree_view(self):
        sgf_game = gosgf.Sgf_game.from_string(SAMPLE_SGF_VAR)
        root = sgf_game.get_root()
        self.assertIsInstance(root, gosgf.Tree_node)
        self.assertIs(root.parent, None)
        self.assertIs(root.owner, sgf_game)
        self.assertEqual(len(root), 1)
        self.assertEqual(root[0].get_raw('B'), "dg")
        self.assertTrue(root)
        self.assertEqual(root.index(root[0]), 0)

        branchnode = root[0][0][0][0]
        self.assertIsInstance(branchnode, gosgf.Tree_node)
        self.assertIs(branchnode.parent, root[0][0][0])
        self.assertIs(branchnode.owner, sgf_game)
        self.assertEqual(len(branchnode), 2)
        self.assertIs(branchnode[1], branchnode[-1])
        self.assertEqual(branchnode[:1], [branchnode[0]])
        self.assertEqual([node for node in branchnode],
                       [branchnode[0], branchnode[1]])
        with self.assertRaises(IndexError):
            branchnode[2]
        self.assertEqual(branchnode[0].get_raw('B'), "ia")
        self.assertEqual(branchnode[1].get_raw('B'), "ib")
        self.assertEqual(branchnode.index(branchnode[0]), 0)
        self.assertEqual(branchnode.index(branchnode[1]), 1)

        self.assertEqual(len(branchnode[1][0]), 2)

        leaf = branchnode[1][0][1]
        self.assertIs(leaf.parent, branchnode[1][0])
        self.assertEqual(len(leaf), 0)
        self.assertFalse(leaf)

        self.assertIs(sgf_game.get_last_node(), root[0][0][0][0][0][0][0])

        # check nothing breaks when first retrieval is by index
        game2 = gosgf.Sgf_game.from_string(SAMPLE_SGF)
        root2 = game2.get_root()
        self.assertEqual(root2[0].get_raw('B'), "dg")

    def test_serialise(self):
        # Doesn't cover transcoding
        sgf_game = gosgf.Sgf_game.from_string(SAMPLE_SGF_VAR)
        serialised = sgf_game.serialise()
        self.assertEqual(serialised, dedent("""\
        (;FF[4]AB[ai][bh][ee]AP[testsuite:0]AW[fd][gc]CA[utf-8]DT[2009-06-06]GM[1]
        KM[7.5]PB[Black engine]PL[B]RE[W+R]SZ[9]VW[];B[dg];C[comment
        on two lines]W[ef]
        ;B[];C[Nonfinal comment]VW[aa:bb](;B[ia];W[ib];B[ic])(;B[ib];W[ic](;B[id])(;
        B[ie])))
        """))
        sgf_game2 = gosgf.Sgf_game.from_string(serialised)
        self.assertEqual(map(str, sgf_game.get_main_sequence()),
                         map(str, sgf_game2.get_main_sequence()))

    def test_serialise_wrap(self):
        sgf_game = gosgf.Sgf_game.from_string(SAMPLE_SGF_VAR)
        serialised = sgf_game.serialise(wrap=None)
        self.assertEqual(serialised, dedent("""\
        (;FF[4]AB[ai][bh][ee]AP[testsuite:0]AW[fd][gc]CA[utf-8]DT[2009-06-06]GM[1]KM[7.5]PB[Black engine]PL[B]RE[W+R]SZ[9]VW[];B[dg];C[comment
        on two lines]W[ef];B[];C[Nonfinal comment]VW[aa:bb](;B[ia];W[ib];B[ic])(;B[ib];W[ic](;B[id])(;B[ie])))
        """))
        sgf_game2 = gosgf.Sgf_game.from_string(serialised)
        self.assertEqual(map(str, sgf_game.get_main_sequence()),
                         map(str, sgf_game2.get_main_sequence()))

    def test_encoding(self):
        g1 = gosgf.Sgf_game(19)
        self.assertEqual(g1.get_charset(), "UTF-8")
        root = g1.get_root()
        self.assertEqual(root.get_encoding(), "UTF-8")
        root.set("C", "£")
        self.assertEqual(root.get("C"), "£")
        self.assertEqual(root.get_raw("C"), "£")
        self.assertEqual(g1.serialise(), dedent("""\
        (;FF[4]C[£]CA[UTF-8]GM[1]SZ[19])
        """))
    
        g2 = gosgf.Sgf_game(19, encoding="iso-8859-1")
        self.assertEqual(g2.get_charset(), "ISO-8859-1")
        root = g2.get_root()
        self.assertEqual(root.get_encoding(), "ISO-8859-1")
        root.set("C", "£")
        self.assertEqual(root.get("C"), "£")
        self.assertEqual(root.get_raw("C"), "\xa3")
        self.assertEqual(g2.serialise(), dedent("""\
        (;FF[4]C[\xa3]CA[ISO-8859-1]GM[1]SZ[19])
        """))
    
        self.assertRaisesRegexp(ValueError, "unknown encoding: unknownencoding",
                              gosgf.Sgf_game, 19, "unknownencoding")
    
    
    def test_loaded_sgf_game_encoding(self):
        g1 = gosgf.Sgf_game.from_string("""
        (;FF[4]C[£]CA[utf-8]GM[1]SZ[19])
        """)
        self.assertEqual(g1.get_charset(), "UTF-8")
        root = g1.get_root()
        self.assertEqual(root.get_encoding(), "UTF-8")
        self.assertEqual(root.get("C"), "£")
        self.assertEqual(root.get_raw("C"), "£")
        self.assertEqual(g1.serialise(), dedent("""\
        (;FF[4]C[£]CA[utf-8]GM[1]SZ[19])
        """))
    
        g2 = gosgf.Sgf_game.from_string("""
        (;FF[4]C[\xa3]CA[iso-8859-1]GM[1]SZ[19])
        """)
        self.assertEqual(g2.get_charset(), "ISO-8859-1")
        root = g2.get_root()
        self.assertEqual(root.get_encoding(), "ISO-8859-1")
        self.assertEqual(root.get("C"), "£")
        self.assertEqual(root.get_raw("C"), "\xa3")
        self.assertEqual(g2.serialise(), dedent("""\
        (;FF[4]C[\xa3]CA[iso-8859-1]GM[1]SZ[19])
        """))
    
        g3 = gosgf.Sgf_game.from_string("""
        (;FF[4]C[\xa3]GM[1]SZ[19])
        """)
        self.assertEqual(g3.get_charset(), "ISO-8859-1")
        root = g3.get_root()
        self.assertEqual(root.get_encoding(), "ISO-8859-1")
        self.assertEqual(root.get("C"), "£")
        self.assertEqual(root.get_raw("C"), "\xa3")
        self.assertEqual(g3.serialise(), dedent("""\
        (;FF[4]C[\xa3]GM[1]SZ[19])
        """))
    
        # This is invalidly encoded. get() notices, but serialise() doesn't care.
        g4 = gosgf.Sgf_game.from_string("""
        (;FF[4]C[\xa3]CA[utf-8]GM[1]SZ[19])
        """)
        self.assertEqual(g4.get_charset(), "UTF-8")
        root = g4.get_root()
        self.assertEqual(root.get_encoding(), "UTF-8")
        self.assertRaises(UnicodeDecodeError, root.get, "C")
        self.assertEqual(root.get_raw("C"), "\xa3")
        self.assertEqual(g4.serialise(), dedent("""\
        (;FF[4]C[\xa3]CA[utf-8]GM[1]SZ[19])
        """))
    
        self.assertRaisesRegexp(
            ValueError, "unknown encoding: unknownencoding",
            gosgf.Sgf_game.from_string, """
            (;FF[4]CA[unknownencoding]GM[1]SZ[19])
            """)
    
    def test_override_encoding(self):
        g1 = gosgf.Sgf_game.from_string("""
        (;FF[4]C[£]CA[iso-8859-1]GM[1]SZ[19])
        """, override_encoding="utf-8")
        root = g1.get_root()
        self.assertEqual(root.get_encoding(), "UTF-8")
        self.assertEqual(root.get("C"), "£")
        self.assertEqual(root.get_raw("C"), "£")
        self.assertEqual(g1.serialise(), dedent("""\
        (;FF[4]C[£]CA[UTF-8]GM[1]SZ[19])
        """))
    
        g2 = gosgf.Sgf_game.from_string("""
        (;FF[4]C[\xa3]CA[utf-8]GM[1]SZ[19])
        """, override_encoding="iso-8859-1")
        root = g2.get_root()
        self.assertEqual(root.get_encoding(), "ISO-8859-1")
        self.assertEqual(root.get("C"), "£")
        self.assertEqual(root.get_raw("C"), "\xa3")
        self.assertEqual(g2.serialise(), dedent("""\
        (;FF[4]C[\xa3]CA[ISO-8859-1]GM[1]SZ[19])
        """))
    
    def test_serialise_transcoding(self):
        g1 = gosgf.Sgf_game.from_string("""
        (;FF[4]C[£]CA[utf-8]GM[1]SZ[19])
        """)
        self.assertEqual(g1.serialise(), dedent("""\
        (;FF[4]C[£]CA[utf-8]GM[1]SZ[19])
        """))
        g1.get_root().set("CA", "latin-1")
        self.assertEqual(g1.serialise(), dedent("""\
        (;FF[4]C[\xa3]CA[latin-1]GM[1]SZ[19])
        """))
        g1.get_root().set("CA", "unknown")
        self.assertRaisesRegexp(ValueError, "unsupported charset: \['unknown']",
                              g1.serialise)
    
        # improperly-encoded from the start
        g2 = gosgf.Sgf_game.from_string("""
        (;FF[4]C[£]CA[ascii]GM[1]SZ[19])
        """)
        self.assertEqual(g2.serialise(), dedent("""\
        (;FF[4]C[£]CA[ascii]GM[1]SZ[19])
        """))
        g2.get_root().set("CA", "utf-8")
        self.assertRaises(UnicodeDecodeError, g2.serialise)
    
        g3 = gosgf.Sgf_game.from_string("""
        (;FF[4]C[Δ]CA[utf-8]GM[1]SZ[19])
        """)
        g3.get_root().unset("CA")
        self.assertRaises(UnicodeEncodeError, g3.serialise)
    
    def test_tree_mutation(self):
        sgf_game = gosgf.Sgf_game(9)
        root = sgf_game.get_root()
        n1 = root.new_child()
        n1.set("N", "n1")
        n2 = root.new_child()
        n2.set("N", "n2")
        n3 = n1.new_child()
        n3.set("N", "n3")
        n4 = root.new_child(1)
        n4.set("N", "n4")
        self.assertEqual(
            sgf_game.serialise(),
            "(;FF[4]CA[UTF-8]GM[1]SZ[9](;N[n1];N[n3])(;N[n4])(;N[n2]))\n")
        self.assertEqual(
            [node.get_raw_property_map() for node in sgf_game.main_sequence_iter()],
            [node.get_raw_property_map() for node in root, root[0], n3])
        self.assertIs(sgf_game.get_last_node(), n3)
    
        n1.delete()
        self.assertEqual(
            sgf_game.serialise(),
            "(;FF[4]CA[UTF-8]GM[1]SZ[9](;N[n4])(;N[n2]))\n")
        self.assertRaises(ValueError, root.delete)
    
    def test_tree_mutation_from_coarse_game(self):
        sgf_game = gosgf.Sgf_game.from_string("(;SZ[9](;N[n1];N[n3])(;N[n2]))")
        root = sgf_game.get_root()
        n4 = root.new_child()
        n4.set("N", "n4")
        n3 = root[0][0]
        self.assertEqual(n3.get("N"), "n3")
        n5 = n3.new_child()
        n5.set("N", "n5")
        self.assertEqual(sgf_game.serialise(),
                       "(;SZ[9](;N[n1];N[n3];N[n5])(;N[n2])(;N[n4]))\n")
        self.assertEqual(
            [node.get_raw_property_map() for node in sgf_game.main_sequence_iter()],
            [node.get_raw_property_map() for node in root, root[0], n3, n5])
        self.assertIs(sgf_game.get_last_node(), n5)
        n3.delete()
        self.assertEqual(sgf_game.serialise(),
                       "(;SZ[9](;N[n1])(;N[n2])(;N[n4]))\n")
        self.assertRaises(ValueError, root.delete)
    
    def test_tree_new_child_with_unexpanded_root_and_index(self):
        sgf_game = gosgf.Sgf_game.from_string("(;SZ[9](;N[n1];N[n3])(;N[n2]))")
        root = sgf_game.get_root()
        n4 = root.new_child(2)
        n4.set("N", "n4")
        self.assertEqual(sgf_game.serialise(),
                       "(;SZ[9](;N[n1];N[n3])(;N[n2])(;N[n4]))\n")
    
    def test_reparent(self):
        g1 = gosgf.Sgf_game.from_string("(;SZ[9](;N[n1];N[n3])(;N[n2]))")
        root = g1.get_root()
        # Test with unexpanded root
        self.assertRaisesRegexp(ValueError, "would create a loop",
                              root.reparent, root)
        n1 = root[0]
        n2 = root[1]
        n3 = root[0][0]
        self.assertEqual(n1.get("N"), "n1")
        self.assertEqual(n2.get("N"), "n2")
        self.assertEqual(n3.get("N"), "n3")
        n3.reparent(n2)
        self.assertEqual(g1.serialise(), "(;SZ[9](;N[n1])(;N[n2];N[n3]))\n")
        n3.reparent(n2)
        self.assertEqual(g1.serialise(), "(;SZ[9](;N[n1])(;N[n2];N[n3]))\n")
        self.assertRaisesRegexp(ValueError, "would create a loop",
                              root.reparent, n3)
        self.assertRaisesRegexp(ValueError, "would create a loop",
                              n3.reparent, n3)
        g2 = gosgf.Sgf_game(9)
        self.assertRaisesRegexp(
            ValueError, "new parent doesn't belong to the same game",
            n3.reparent, g2.get_root())
    
    def test_reparent_index(self):
        g1 = gosgf.Sgf_game.from_string("(;SZ[9](;N[n1];N[n3])(;N[n2]))")
        root = g1.get_root()
        n1 = root[0]
        n2 = root[1]
        n3 = root[0][0]
        self.assertEqual(n1.get("N"), "n1")
        self.assertEqual(n2.get("N"), "n2")
        self.assertEqual(n3.get("N"), "n3")
        n3.reparent(root, index=1)
        self.assertEqual(g1.serialise(), "(;SZ[9](;N[n1])(;N[n3])(;N[n2]))\n")
        n3.reparent(root, index=1)
        self.assertEqual(g1.serialise(), "(;SZ[9](;N[n1])(;N[n3])(;N[n2]))\n")
        n3.reparent(root, index=2)
        self.assertEqual(g1.serialise(), "(;SZ[9](;N[n1])(;N[n2])(;N[n3]))\n")
    
    def test_extend_main_sequence(self):
        g1 = gosgf.Sgf_game(9)
        for i in xrange(6):
            g1.extend_main_sequence().set("N", "e%d" % i)
        self.assertEqual(
            g1.serialise(),
            "(;FF[4]CA[UTF-8]GM[1]SZ[9];N[e0];N[e1];N[e2];N[e3];N[e4];N[e5])\n")
        g2 = gosgf.Sgf_game.from_string("(;SZ[9](;N[n1];N[n3])(;N[n2]))")
        for i in xrange(6):
            g2.extend_main_sequence().set("N", "e%d" % i)
        self.assertEqual(
            g2.serialise(),
            "(;SZ[9](;N[n1];N[n3];N[e0];N[e1];N[e2];N[e3];N[e4];N[e5])(;N[n2]))\n")

    def test_get_sequence_above(self):
        sgf_game = gosgf.Sgf_game.from_string(SAMPLE_SGF_VAR)
        root = sgf_game.get_root()
        branchnode = root[0][0][0][0]
        leaf = branchnode[1][0][1]
        self.assertEqual(sgf_game.get_sequence_above(root), [])

        self.assertEqual(sgf_game.get_sequence_above(branchnode),
                         [root, root[0], root[0][0], root[0][0][0]])

        self.assertEqual(sgf_game.get_sequence_above(leaf),
                         [root, root[0], root[0][0], root[0][0][0],
                          branchnode, branchnode[1], branchnode[1][0]])

        sgf_game2 = gosgf.Sgf_game.from_string(SAMPLE_SGF_VAR)
        self.assertRaisesRegexp(ValueError, "node doesn't belong to this game",
                                sgf_game2.get_sequence_above, leaf)

    def test_get_main_sequence_below(self):
        sgf_game = gosgf.Sgf_game.from_string(SAMPLE_SGF_VAR)
        root = sgf_game.get_root()
        branchnode = root[0][0][0][0]
        leaf = branchnode[1][0][1]
        self.assertEqual(sgf_game.get_main_sequence_below(leaf), [])

        self.assertEqual(sgf_game.get_main_sequence_below(branchnode),
                         [branchnode[0], branchnode[0][0], branchnode[0][0][0]])

        self.assertEqual(sgf_game.get_main_sequence_below(root),
                         [root[0], root[0][0], root[0][0][0], branchnode,
                          branchnode[0], branchnode[0][0], branchnode[0][0][0]])

        sgf_game2 = gosgf.Sgf_game.from_string(SAMPLE_SGF_VAR)
        self.assertRaisesRegexp(ValueError, "node doesn't belong to this game",
                              sgf_game2.get_main_sequence_below, branchnode)

    def test_main_sequence(self):
        sgf_game = gosgf.Sgf_game.from_string(SAMPLE_SGF_VAR)
        root = sgf_game.get_root()

        nodes = list(sgf_game.main_sequence_iter())
        self.assertEqual(len(nodes), 8)
        self.assertIs(root.get_raw_property_map(),
                    nodes[0].get_raw_property_map())
        # Check that main_sequence_iter() optimisation has been used.
        # (Have to call this before making the tree expand.)
        with self.assertRaises(AttributeError):
            nodes[1].parent
    
        tree_nodes = sgf_game.get_main_sequence()
        self.assertEqual(len(tree_nodes), 8)
        self.assertIs(root.get_raw_property_map(),
                    tree_nodes[0].get_raw_property_map())
        self.assertIs(tree_nodes[0], root)
        self.assertIs(tree_nodes[2].parent, tree_nodes[1])
        self.assertIs(sgf_game.get_last_node(), tree_nodes[-1])

        tree_node = root
        for node in nodes:
            self.assertIs(tree_node.get_raw_property_map(),
                        node.get_raw_property_map())
            if tree_node:
                tree_node = tree_node[0]

    def test_find(self):
        sgf_game = gosgf.Sgf_game.from_string(SAMPLE_SGF_VAR)
        root = sgf_game.get_root()
        branchnode = root[0][0][0][0]
        leaf = branchnode[1][0][1]

        self.assertEqual(root.get("VW"), set())
        self.assertIs(root.find("VW"), root)
        self.assertRaises(KeyError, root[0].get, "VW")
        self.assertEqual(root[0].find_property("VW"), set())
        self.assertIs(root[0].find("VW"), root)

        self.assertEqual(branchnode.get("VW"),
                       set([(7, 0), (7, 1), (8, 0), (8, 1)]))
        self.assertIs(branchnode.find("VW"), branchnode)
        self.assertEqual(branchnode.find_property("VW"),
                       set([(7, 0), (7, 1), (8, 0), (8, 1)]))

        self.assertRaises(KeyError, leaf.get, "VW")
        self.assertIs(leaf.find("VW"), branchnode)
        self.assertEqual(leaf.find_property("VW"),
                       set([(7, 0), (7, 1), (8, 0), (8, 1)]))

        self.assertIs(leaf.find("XX"), None)
        self.assertRaises(KeyError, leaf.find_property, "XX")

    def test_node_set_raw(self):
        sgf_game = gosgf.Sgf_game.from_string(dedent(r"""
        (;AP[testsuite:0]CA[utf-8]DT[2009-06-06]FF[4]GM[1]KM[7.5]
        PB[Black engine]PW[White engine]RE[W+R]SZ[9]
        AB[ai][bh][ee]AW[fd][gc]BM[2]VW[]
        PL[B]
        C[123abc]
        ;B[dg]C[first move])
        """))
        root = sgf_game.get_root()
        self.assertEqual(root.get_raw('RE'), "W+R")
        root.set_raw('RE', "W+2.5")
        self.assertEqual(root.get_raw('RE'), "W+2.5")
        self.assertRaises(KeyError, root.get_raw, 'XX')
        root.set_raw('XX', "xyz")
        self.assertEqual(root.get_raw('XX'), "xyz")
    
        root.set_raw_list('XX', ("abc", "def"))
        self.assertEqual(root.get_raw('XX'), "abc")
        self.assertEqual(root.get_raw_list('XX'), ["abc", "def"])
    
        self.assertRaisesRegexp(ValueError, "empty property list",
                              root.set_raw_list, 'B', [])
    
        values = ["123", "456"]
        root.set_raw_list('YY', values)
        self.assertEqual(root.get_raw_list('YY'), ["123", "456"])
        values.append("789")
        self.assertEqual(root.get_raw_list('YY'), ["123", "456"])
    
        self.assertRaisesRegexp(ValueError, "ill-formed property identifier",
                              root.set_raw, 'Black', "aa")
        self.assertRaisesRegexp(ValueError, "ill-formed property identifier",
                              root.set_raw_list, 'Black', ["aa"])
    
        root.set_raw('C', "foo\\]bar")
        self.assertEqual(root.get_raw('C'), "foo\\]bar")
        root.set_raw('C', "abc\\\\")
        self.assertEqual(root.get_raw('C'), "abc\\\\")
        self.assertRaisesRegexp(ValueError, "ill-formed raw property value",
                              root.set_raw, 'C', "foo]bar")
        self.assertRaisesRegexp(ValueError, "ill-formed raw property value",
                              root.set_raw, 'C', "abc\\")
        self.assertRaisesRegexp(ValueError, "ill-formed raw property value",
                              root.set_raw_list, 'C', ["abc", "de]f"])
    
        root.set_raw('C', "foo\\]bar\\\nbaz")
        self.assertEqual(root.get('C'), "foo]barbaz")

    def test_node_aliasing(self):
        # Check that node objects retrieved by different means use the same
        # property map.

        sgf_game = gosgf.Sgf_game.from_string(dedent(r"""
        (;C[root];C[node 1])
        """))
        root = sgf_game.get_root()
        plain_node = list(sgf_game.main_sequence_iter())[1]
        tree_node = root[0]
        # Check the main_sequence_iter() optimisation was used, otherwise this test
        # isn't checking what it's supposed to.
        self.assertIsNot(tree_node, plain_node)
        self.assertIs(tree_node.__class__, gosgf.Tree_node)
        self.assertIs(plain_node.__class__, gosgf.Node)

        self.assertEqual(tree_node.get_raw('C'), "node 1")
        tree_node.set_raw('C', r"test\value")
        self.assertEqual(tree_node.get_raw('C'), r"test\value")
        self.assertEqual(plain_node.get_raw('C'), r"test\value")

        plain_node.set_raw_list('XX', ["1", "2", "3"])
        self.assertEqual(tree_node.get_raw_list('XX'), ["1", "2", "3"])

    def test_node_set(self):
        sgf_game = gosgf.Sgf_game.from_string("(;FF[4]GM[1]SZ[9])")
        root = sgf_game.get_root()
        root.set("KO", True)
        root.set("KM", 0.5)
        root.set('DD', [(3, 4), (5, 6)])
        root.set('AB', set([(0, 0), (1, 1), (4, 4)]))
        root.set('TW', set())
        root.set('XX', "nonsense [none]sense more n\\onsens\\e")
    
        self.assertEqual(sgf_game.serialise(), dedent("""\
        (;FF[4]AB[ai][bh][ee]DD[ef][gd]GM[1]KM[0.5]KO[]SZ[9]TW[]
        XX[nonsense [none\\]sense more n\\\\onsens\\\\e])
        """))
    
    def test_node_unset(self):
        sgf_game = gosgf.Sgf_game.from_string("(;FF[4]GM[1]SZ[9]HA[3])")
        root = sgf_game.get_root()
        self.assertEqual(root.get('HA'), 3)
        root.unset('HA')
        self.assertRaises(KeyError, root.unset, 'PL')
        self.assertEqual(sgf_game.serialise(),
                       "(;FF[4]GM[1]SZ[9])\n")
    
    def test_set_and_unset_size(self):
        g1 = gosgf.Sgf_game.from_string("(;FF[4]GM[1]SZ[9]HA[3])")
        root1 = g1.get_root()
        self.assertRaisesRegexp(ValueError, "changing size is not permitted",
                              root1.set, "SZ", 19)
        root1.set("SZ", 9)
        self.assertRaisesRegexp(ValueError, "changing size is not permitted",
                              root1.unset, "SZ")
        g2 = gosgf.Sgf_game.from_string("(;FF[4]GM[1]SZ[19]HA[3])")
        root2 = g2.get_root()
        root2.unset("SZ")
        root2.set("SZ", 19)
    
    def test_set_and_unset_charset(self):
        g1 = gosgf.Sgf_game.from_string("(;FF[4]CA[utf-8]GM[1]SZ[9]HA[3])")
        self.assertEqual(g1.get_charset(), "UTF-8")
        root1 = g1.get_root()
        root1.unset("CA")
        self.assertEqual(g1.get_charset(), "ISO-8859-1")
        root1.set("CA", "iso-8859-1")
        self.assertEqual(g1.get_charset(), "ISO-8859-1")
        root1.set("CA", "ascii")
        self.assertEqual(g1.get_charset(), "ASCII")
        root1.set("CA", "unknownencoding")
        self.assertRaisesRegexp(ValueError,
                              "no codec available for CA unknownencoding",
                              g1.get_charset)
    
    def test_node_set_move(self):
        sgf_game = gosgf.Sgf_game.from_string("(;FF[4]GM[1]SZ[9];B[aa];B[bb])")
        root, n1, n2 = sgf_game.get_main_sequence()
        self.assertEqual(root.get_move(), (None, None))
        root.set_move('b', (1, 1))
        n1.set_move('w', (1, 2))
        n2.set_move('b', None)
        self.assertEqual(root.get('B'), (1, 1))
        self.assertRaises(KeyError, root.get, 'W')
        self.assertEqual(n1.get('W'), (1, 2))
        self.assertRaises(KeyError, n1.get, 'B')
        self.assertEqual(n2.get('B'), None)
        self.assertRaises(KeyError, n2.get, 'W')

    def test_node_setup_stones(self):
        sgf_game = gosgf.Sgf_game.from_string("(;FF[4]GM[1]SZ[9]AW[aa:bb])")
        root = sgf_game.get_root()
        root.set_setup_stones(
            [(1, 2), (3, 4)],
            set(),
            [(1, 3), (4, 5)],
            )
        self.assertEqual(root.get('AB'), set([(1, 2), (3, 4)]))
        self.assertRaises(KeyError, root.get, 'AW')
        self.assertEqual(root.get('AE'), set([(1, 3), (4, 5)]))

    def test_add_comment_text(self):
        sgf_game = gosgf.Sgf_game(9)
        root = sgf_game.get_root()
        root.add_comment_text("hello\nworld")
        self.assertEqual(root.get('C'), "hello\nworld")
        root.add_comment_text("hello\naga]in")
        self.assertEqual(root.get('C'), "hello\nworld\n\nhello\naga]in")
