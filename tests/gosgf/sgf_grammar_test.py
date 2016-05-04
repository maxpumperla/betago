"""Tests for sgf_grammar.py."""

import unittest

from betago.gosgf import sgf_grammar


class SgfGrammarTestCase(unittest.TestCase):
    def test_is_valid_property_identifier(tc):
        ivpi = sgf_grammar.is_valid_property_identifier
        tc.assertIs(ivpi(b"B"), True)
        tc.assertIs(ivpi(b"PB"), True)
        tc.assertIs(ivpi(b"ABCDEFGH"), True)
        tc.assertIs(ivpi(b"ABCDEFGHI"), False)
        tc.assertIs(ivpi(b""), False)
        tc.assertIs(ivpi(b"b"), False)
        tc.assertIs(ivpi(b"Player"), False)
        tc.assertIs(ivpi(b"P2"), False)
        tc.assertIs(ivpi(b" PB"), False)
        tc.assertIs(ivpi(b"PB "), False)
        tc.assertIs(ivpi(b"P B"), False)
        tc.assertIs(ivpi(b"PB\x00"), False)

    def test_is_valid_property_value(tc):
        ivpv = sgf_grammar.is_valid_property_value
        tc.assertIs(ivpv(b""), True)
        tc.assertIs(ivpv(b"hello world"), True)
        tc.assertIs(ivpv(b"hello\nworld"), True)
        tc.assertIs(ivpv(b"hello \x00 world"), True)
        tc.assertIs(ivpv(b"hello \xa3 world"), True)
        tc.assertIs(ivpv(b"hello \xc2\xa3 world"), True)
        tc.assertIs(ivpv(b"hello \\-) world"), True)
        tc.assertIs(ivpv(b"hello (;[) world"), True)
        tc.assertIs(ivpv(b"[hello world]"), False)
        tc.assertIs(ivpv(b"hello ] world"), False)
        tc.assertIs(ivpv(b"hello \\] world"), True)
        tc.assertIs(ivpv(b"hello world \\"), False)
        tc.assertIs(ivpv(b"hello world \\\\"), True)
        tc.assertIs(ivpv(b"x" * 70000), True)

    def test_tokeniser(tc):
        tokenise = sgf_grammar.tokenise

        tc.assertEqual(tokenise(b"(;B[ah][]C[a\xa3b])")[0],
                       [('D', b'('),
                        ('D', b';'),
                        ('I', b'B'),
                        ('V', b'ah'),
                        ('V', b''),
                        ('I', b'C'),
                        ('V', b'a\xa3b'),
                        ('D', b')')])

        def check_complete(s, *args):
            tokens, tail_index = tokenise(s, *args)
            tc.assertEqual(tail_index, len(s))
            return len(tokens)

        def check_incomplete(s, *args):
            tokens, tail_index = tokenise(s, *args)
            return len(tokens), tail_index

        # check surrounding junk
        tc.assertEqual(check_complete(b""), 0)
        tc.assertEqual(check_complete(b"junk (;B[ah])"), 5)
        tc.assertEqual(check_incomplete(b"junk"), (0, 0))
        tc.assertEqual(check_incomplete(b"junk (B[ah])"), (0, 0))
        tc.assertEqual(check_incomplete(b"(;B[ah]) junk"), (5, 8))

        # check paren-balance count
        tc.assertEqual(check_incomplete(b"(; ))(([ag]B C[ah])"), (3, 4))
        tc.assertEqual(check_incomplete(b"(;( )) (;)"), (5, 6))
        tc.assertEqual(check_incomplete(b"(;(()())) (;)"), (9, 9))

        # check start_position
        tc.assertEqual(check_complete(b"(; ))(;B[ah])", 4), 5)
        tc.assertEqual(check_complete(b"(; ))junk (;B[ah])", 4), 5)

        tc.assertEqual(check_complete(b"(;XX[abc][def]KO[];B[bc])"), 11)
        tc.assertEqual(check_complete(b"( ;XX[abc][def]KO[];B[bc])"), 11)
        tc.assertEqual(check_complete(b"(; XX[abc][def]KO[];B[bc])"), 11)
        tc.assertEqual(check_complete(b"(;XX [abc][def]KO[];B[bc])"), 11)
        tc.assertEqual(check_complete(b"(;XX[abc] [def]KO[];B[bc])"), 11)
        tc.assertEqual(check_complete(b"(;XX[abc][def] KO[];B[bc])"), 11)
        tc.assertEqual(check_complete(b"(;XX[abc][def]KO [];B[bc])"), 11)
        tc.assertEqual(check_complete(b"(;XX[abc][def]KO[] ;B[bc])"), 11)
        tc.assertEqual(check_complete(b"(;XX[abc][def]KO[]; B[bc])"), 11)
        tc.assertEqual(check_complete(b"(;XX[abc][def]KO[];B [bc])"), 11)
        tc.assertEqual(check_complete(b"(;XX[abc][def]KO[];B[bc] )"), 11)

        tc.assertEqual(check_complete(b"( ;\nB\t[ah]\f[ef]\v)"), 6)
        tc.assertEqual(check_complete(b"(;[Ran\xc2\xa3dom :\nstu@ff][ef]"), 4)
        tc.assertEqual(check_complete(b"(;[ah)])"), 4)

        tc.assertEqual(check_incomplete(b"(;B[ag"), (3, 3))
        tc.assertEqual(check_incomplete(b"(;B[ag)"), (3, 3))
        tc.assertEqual(check_incomplete(b"(;AddBlack[ag])"), (3, 3))
        tc.assertEqual(check_incomplete(b"(;+B[ag])"), (2, 2))
        tc.assertEqual(check_incomplete(b"(;B+[ag])"), (3, 3))
        tc.assertEqual(check_incomplete(b"(;B[ag]+)"), (4, 7))

        tc.assertEqual(check_complete(r"(;[ab \] cd][ef]".encode('ascii')), 4)
        tc.assertEqual(check_complete(r"(;[ab \] cd\\][ef]".encode('ascii')), 4)
        tc.assertEqual(check_complete(r"(;[ab \] cd\\\\][ef]".encode('ascii')), 4)
        tc.assertEqual(check_complete(r"(;[ab \] \\\] cd][ef]".encode('ascii')), 4)
        tc.assertEqual(check_incomplete(r"(;B[ag\])".encode('ascii')), (3, 3))
        tc.assertEqual(check_incomplete(r"(;B[ag\\\])".encode('ascii')), (3, 3))

    def test_parser_structure(tc):
        parse_sgf_game = sgf_grammar.parse_sgf_game

        def shape(s):
            coarse_game = parse_sgf_game(s)
            return len(coarse_game.sequence), len(coarse_game.children)

        tc.assertEqual(shape(b"(;C[abc]KO[];B[bc])"), (2, 0))
        tc.assertEqual(shape(b"initial junk (;C[abc]KO[];B[bc])"), (2, 0))
        tc.assertEqual(shape(b"(;C[abc]KO[];B[bc]) final junk"), (2, 0))
        tc.assertEqual(shape(b"(;C[abc]KO[];B[bc]) (;B[ag])"), (2, 0))

        tc.assertRaisesRegexp(ValueError, "no SGF data found",
                              parse_sgf_game, b"")
        tc.assertRaisesRegexp(ValueError, "no SGF data found",
                              parse_sgf_game, b"junk")
        tc.assertRaisesRegexp(ValueError, "no SGF data found",
                              parse_sgf_game, b"()")
        tc.assertRaisesRegexp(ValueError, "no SGF data found",
                              parse_sgf_game, b"(B[ag])")
        tc.assertRaisesRegexp(ValueError, "no SGF data found",
                              parse_sgf_game, b"B[ag]")
        tc.assertRaisesRegexp(ValueError, "no SGF data found",
                              parse_sgf_game, b"[ag]")

        tc.assertEqual(shape(b"(;C[abc]AB[ab][bc];B[bc])"), (2, 0))
        tc.assertEqual(shape(b"(;C[abc] AB[ab]\n[bc]\t;B[bc])"), (2, 0))
        tc.assertEqual(shape(b"(;C[abc]KO[];;B[bc])"), (3, 0))
        tc.assertEqual(shape(b"(;)"), (1, 0))

        tc.assertRaisesRegexp(ValueError, "property with no values",
                              parse_sgf_game, b"(;B)")
        tc.assertRaisesRegexp(ValueError, "unexpected value",
                              parse_sgf_game, b"(;[ag])")
        tc.assertRaisesRegexp(ValueError, "unexpected value",
                              parse_sgf_game, b"(;[ag][ah])")
        tc.assertRaisesRegexp(ValueError, "unexpected value",
                              parse_sgf_game, b"(;[B][ag])")
        tc.assertRaisesRegexp(ValueError, "unexpected end of SGF data",
                              parse_sgf_game, b"(;B[ag]")
        tc.assertRaisesRegexp(ValueError, "unexpected end of SGF data",
                              parse_sgf_game, b"(;B[ag][)]")
        tc.assertRaisesRegexp(ValueError, "property with no values",
                              parse_sgf_game, b"(;B;W[ah])")
        tc.assertRaisesRegexp(ValueError, "unexpected value",
                              parse_sgf_game, b"(;B[ag](;[ah]))")
        tc.assertRaisesRegexp(ValueError, "property with no values",
                              parse_sgf_game, b"(;B W[ag])")

    def test_parser_tree_structure(tc):
        parse_sgf_game = sgf_grammar.parse_sgf_game

        def shape(s):
            coarse_game = parse_sgf_game(s)
            return len(coarse_game.sequence), len(coarse_game.children)

        tc.assertEqual(shape(b"(;C[abc]AB[ab](;B[bc]))"), (1, 1))
        tc.assertEqual(shape(b"(;C[abc]AB[ab](;B[bc])))"), (1, 1))
        tc.assertEqual(shape(b"(;C[abc]AB[ab](;B[bc])(;B[bd]))"), (1, 2))

        def shapetree(s):
            def _shapetree(coarse_game):
                return (
                    len(coarse_game.sequence),
                    [_shapetree(pg) for pg in coarse_game.children])
            return _shapetree(parse_sgf_game(s))

        tc.assertEqual(shapetree(b"(;C[abc]AB[ab](;B[bc])))"),
                       (1, [(1, [])])
                       )
        tc.assertEqual(shapetree(b"(;C[abc]AB[ab](;B[bc]))))"),
                       (1, [(1, [])])
                       )
        tc.assertEqual(shapetree(b"(;C[abc]AB[ab](;B[bc])(;B[bd])))"),
                       (1, [(1, []), (1, [])])
                       )
        tc.assertEqual(shapetree(b"""
            (;C[abc]AB[ab];C[];C[]
              (;B[bc])
              (;B[bd];W[ca] (;B[da])(;B[db];W[ea]) )
            )"""),
            (3, [
                (1, []),
                (2, [(1, []), (2, [])])
            ])
        )

        tc.assertRaisesRegexp(ValueError, "unexpected end of SGF data",
                              parse_sgf_game, b"(;B[ag];W[ah](;B[ai])")
        tc.assertRaisesRegexp(ValueError, "empty sequence",
                              parse_sgf_game, b"(;B[ag];())")
        tc.assertRaisesRegexp(ValueError, "empty sequence",
                              parse_sgf_game, b"(;B[ag]())")
        tc.assertRaisesRegexp(ValueError, "empty sequence",
                              parse_sgf_game, b"(;B[ag]((;W[ah])(;W[ai]))")
        tc.assertRaisesRegexp(ValueError, "unexpected node",
                              parse_sgf_game, b"(;B[ag];W[ah](;B[ai]);W[bd])")
        tc.assertRaisesRegexp(ValueError, "property value outside a node",
                              parse_sgf_game, b"(;B[ag];(W[ah];B[ai]))")
        tc.assertRaisesRegexp(ValueError, "property value outside a node",
                              parse_sgf_game, b"(;B[ag](;W[ah];)B[ai])")
        tc.assertRaisesRegexp(ValueError, "property value outside a node",
                              parse_sgf_game, b"(;B[ag](;W[ah])(B[ai]))")

    def test_parser_properties(tc):
        parse_sgf_game = sgf_grammar.parse_sgf_game

        def props(s):
            coarse_game = parse_sgf_game(s)
            return coarse_game.sequence

        tc.assertEqual(props(b"(;C[abc]KO[]AB[ai][bh][ee];B[ bc])"),
                       [{b'C': [b'abc'], b'KO': [b''], b'AB': [b'ai', b'bh', b'ee']},
                        {b'B': [b' bc']}])

        tc.assertEqual(props(r"(;C[ab \] \) cd\\])".encode('ascii')),
                       [{b'C': [r"ab \] \) cd\\".encode('ascii')]}])

        tc.assertEqual(props(b"(;XX[1]YY[2]XX[3]YY[4])"),
                       [{b'XX': [b'1', b'3'], b'YY' : [b'2', b'4']}])

    def test_parse_sgf_collection(tc):
        parse_sgf_collection = sgf_grammar.parse_sgf_collection

        tc.assertRaisesRegexp(ValueError, "no SGF data found",
                              parse_sgf_collection, b"")
        tc.assertRaisesRegexp(ValueError, "no SGF data found",
                              parse_sgf_collection, b"()")

        games = parse_sgf_collection(b"(;C[abc]AB[ab];X[];X[](;B[bc]))")
        tc.assertEqual(len(games), 1)
        tc.assertEqual(len(games[0].sequence), 3)

        games = parse_sgf_collection(b"(;X[1];X[2];X[3](;B[bc])) (;Y[1];Y[2])")
        tc.assertEqual(len(games), 2)
        tc.assertEqual(len(games[0].sequence), 3)
        tc.assertEqual(len(games[1].sequence), 2)

        games = parse_sgf_collection(
            b"dummy (;X[1];X[2];X[3](;B[bc])) junk (;Y[1];Y[2]) Nonsense")
        tc.assertEqual(len(games), 2)
        tc.assertEqual(len(games[0].sequence), 3)
        tc.assertEqual(len(games[1].sequence), 2)

        games = parse_sgf_collection(
            b"(( (;X[1];X[2];X[3](;B[bc])) ();) (;Y[1];Y[2]) )(Nonsense")
        tc.assertEqual(len(games), 2)
        tc.assertEqual(len(games[0].sequence), 3)
        tc.assertEqual(len(games[1].sequence), 2)

        with tc.assertRaises(ValueError) as ar:
            parse_sgf_collection(
                b"(( (;X[1];X[2];X[3](;B[bc])) ();) (;Y[1];Y[2]")
        tc.assertEqual(str(ar.exception),
                       "error parsing game 1: unexpected end of SGF data")

    def test_parse_compose(tc):
        pc = sgf_grammar.parse_compose
        tc.assertEqual(pc(b"word"), (b"word", None))
        tc.assertEqual(pc(b"word:"), (b"word", b""))
        tc.assertEqual(pc(b"word:?"), (b"word", b"?"))
        tc.assertEqual(pc(b"word:123"), (b"word", b"123"))
        tc.assertEqual(pc(b"word:123:456"), (b"word", b"123:456"))
        tc.assertEqual(pc(b":123"), (b"", b"123"))
        tc.assertEqual(pc(r"word\:more".encode('ascii')), (r"word\:more".encode('ascii'), None))
        tc.assertEqual(pc(r"word\:more:?".encode('ascii')), (r"word\:more".encode('ascii'), b"?"))
        tc.assertEqual(pc(r"word\\:more:?".encode('ascii')), (b"word\\\\", b"more:?"))
        tc.assertEqual(pc(r"word\\\:more:?".encode('ascii')),
                       (r"word\\\:more".encode('ascii'), b"?"))
        tc.assertEqual(pc(b"word\\\nmore:123"), (b"word\\\nmore", b"123"))

    def test_text_value(tc):
        text_value = sgf_grammar.text_value
        tc.assertEqual(text_value(b"abc "), b"abc ")
        tc.assertEqual(text_value(b"ab c"), b"ab c")
        tc.assertEqual(text_value(b"ab\tc"), b"ab c")
        tc.assertEqual(text_value(b"ab \tc"), b"ab  c")
        tc.assertEqual(text_value(b"ab\nc"), b"ab\nc")
        tc.assertEqual(text_value(b"ab\\\nc"), b"abc")
        tc.assertEqual(text_value(b"ab\\\\\nc"), b"ab\\\nc")
        tc.assertEqual(text_value(b"ab\xa0c"), b"ab\xa0c")

        tc.assertEqual(text_value(b"ab\rc"), b"ab\nc")
        tc.assertEqual(text_value(b"ab\r\nc"), b"ab\nc")
        tc.assertEqual(text_value(b"ab\n\rc"), b"ab\nc")
        tc.assertEqual(text_value(b"ab\r\n\r\nc"), b"ab\n\nc")
        tc.assertEqual(text_value(b"ab\r\n\r\n\rc"), b"ab\n\n\nc")
        tc.assertEqual(text_value(b"ab\\\r\nc"), b"abc")
        tc.assertEqual(text_value(b"ab\\\n\nc"), b"ab\nc")

        tc.assertEqual(text_value(b"ab\\\tc"), b"ab c")

        # These can't actually appear as SGF PropValues; anything sane will do
        tc.assertEqual(text_value(b"abc\\"), b"abc")
        tc.assertEqual(text_value(b"abc]"), b"abc]")

    def test_simpletext_value(tc):
        simpletext_value = sgf_grammar.simpletext_value
        tc.assertEqual(simpletext_value(b"abc "), b"abc ")
        tc.assertEqual(simpletext_value(b"ab c"), b"ab c")
        tc.assertEqual(simpletext_value(b"ab\tc"), b"ab c")
        tc.assertEqual(simpletext_value(b"ab \tc"), b"ab  c")
        tc.assertEqual(simpletext_value(b"ab\nc"), b"ab c")
        tc.assertEqual(simpletext_value(b"ab\\\nc"), b"abc")
        tc.assertEqual(simpletext_value(b"ab\\\\\nc"), b"ab\\ c")
        tc.assertEqual(simpletext_value(b"ab\xa0c"), b"ab\xa0c")

        tc.assertEqual(simpletext_value(b"ab\rc"), b"ab c")
        tc.assertEqual(simpletext_value(b"ab\r\nc"), b"ab c")
        tc.assertEqual(simpletext_value(b"ab\n\rc"), b"ab c")
        tc.assertEqual(simpletext_value(b"ab\r\n\r\nc"), b"ab  c")
        tc.assertEqual(simpletext_value(b"ab\r\n\r\n\rc"), b"ab   c")
        tc.assertEqual(simpletext_value(b"ab\\\r\nc"), b"abc")
        tc.assertEqual(simpletext_value(b"ab\\\n\nc"), b"ab c")

        tc.assertEqual(simpletext_value(b"ab\\\tc"), b"ab c")

        # These can't actually appear as SGF PropValues; anything sane will do
        tc.assertEqual(simpletext_value(b"abc\\"), b"abc")
        tc.assertEqual(simpletext_value(b"abc]"), b"abc]")

    def test_escape_text(tc):
        tc.assertEqual(sgf_grammar.escape_text(b"abc"), b"abc")
        tc.assertEqual(sgf_grammar.escape_text(r"a\bc".encode('ascii')), r"a\\bc".encode('ascii'))
        tc.assertEqual(sgf_grammar.escape_text(r"ab[c]".encode('ascii')),
                       r"ab[c\]".encode('ascii'))
        tc.assertEqual(sgf_grammar.escape_text(r"a\]bc".encode('ascii')),
                       r"a\\\]bc".encode('ascii'))

    def test_text_roundtrip(tc):
        def roundtrip(s):
            return sgf_grammar.text_value(sgf_grammar.escape_text(s))
        tc.assertEqual(roundtrip(b"abc"), b"abc")
        tc.assertEqual(roundtrip(r"a\bc".encode('ascii')), r"a\bc".encode('ascii'))
        tc.assertEqual(roundtrip(b"abc\\"), b"abc\\")
        tc.assertEqual(roundtrip(b"ab]c"), b"ab]c")
        tc.assertEqual(roundtrip(b"abc]"), b"abc]")
        tc.assertEqual(roundtrip(r"abc\]".encode('ascii')), r"abc\]".encode('ascii'))
        tc.assertEqual(roundtrip(b"ab\nc"), b"ab\nc")
        tc.assertEqual(roundtrip(b"ab\n  c"), b"ab\n  c")

        tc.assertEqual(roundtrip(b"ab\tc"), b"ab c")
        tc.assertEqual(roundtrip(b"ab\r\nc\n"), b"ab\nc\n")

    def test_serialise_game_tree(tc):
        serialised = (b"(;AB[aa][ab][ac]C[comment \xa3];W[ab];C[];C[]"
                      b"(;B[bc])(;B[bd];W[ca](;B[da])(;B[db];\n"
                      b"W[ea])))\n")
        coarse_game = sgf_grammar.parse_sgf_game(serialised)
        tc.assertEqual(sgf_grammar.serialise_game_tree(coarse_game), serialised)
        tc.assertEqual(sgf_grammar.serialise_game_tree(coarse_game, wrap=None),
                       serialised.replace(b"\n", b"")+b"\n")

