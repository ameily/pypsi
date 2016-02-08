
from pypsi.cmdline import *
from pypsi.features import BashFeatures
from nose.tools import *


OPERATORS = ('>', '<', '>>', '&', '&&', '|', '||', ';')


class TestCmdlineTokenize(object):

    def setUp(self):
        self.parser = StatementParser(BashFeatures())

    def test_simple(self):
        tokens = self.parser.tokenize("echo \thello")
        assert_equal(tokens, [
            StringToken(0, "echo"),
            WhitespaceToken(1),
            StringToken(2, "hello")
        ])

    def test_closed_single_quote(self):
        assert_equal(
            self.parser.tokenize("echo 'hello'"), [
                StringToken(0, "echo"),
                WhitespaceToken(1),
                StringToken(2, "hello", quote="'")
            ]
        )

    def test_closed_double_quote(self):
        assert_equal(
            self.parser.tokenize("echo \"hello\""), [
                StringToken(0, "echo"),
                WhitespaceToken(1),
                StringToken(2, "hello", quote="\"")
            ]
        )

    def test_adjacent_double_quotes(self):
        assert_equal(
            self.parser.tokenize("echo \"hello\"\"world\""), [
                StringToken(0, "echo"),
                WhitespaceToken(1),
                StringToken(2, "hello", quote="\""),
                StringToken(3, "world", quote="\"")
            ]
        )

    def test_adjacent_single_quotes(self):
        assert_equal(
            self.parser.tokenize("echo 'hello''world'"), [
                StringToken(0, "echo"),
                WhitespaceToken(1),
                StringToken(2, "hello", quote="'"),
                StringToken(3, "world", quote="'")
            ]
        )

    def test_adjacent_mixed_quotes(self):
        assert_equal(
            self.parser.tokenize("echo \"hello\"'world'"), [
                StringToken(0, "echo"),
                WhitespaceToken(1),
                StringToken(2, "hello", quote="\""),
                StringToken(3, "world", quote="'")
            ]
        )

    def test_adjacent_quote(self):
        assert_equal(
            self.parser.tokenize("echo hello\"world\"goodbye"), [
                StringToken(0, "echo"),
                WhitespaceToken(1),
                StringToken(2, "hello"),
                StringToken(3, "world", quote="\""),
                StringToken(4, "goodbye")
            ]
        )

    def test_escaped_whitespace(self):
        assert_equal(
            self.parser.tokenize("echo hello\\ world"), [
                StringToken(0, "echo"),
                WhitespaceToken(1),
                StringToken(2, "hello world"),
            ]
        )

    def test_escaped_quote(self):
        assert_equal(
            self.parser.tokenize("echo hello\\\""), [
                StringToken(0, "echo"),
                WhitespaceToken(1),
                StringToken(2, "hello\""),
            ]
        )

    def test_escaped_nested_quote(self):
        assert_equal(
            self.parser.tokenize("echo \"hello \\\"world\\\"\""), [
                StringToken(0, "echo"),
                WhitespaceToken(1),
                StringToken(2, "hello \"world\"", quote="\""),
            ]
        )

    def test_escaped_bslash(self):
        assert_equal(
            self.parser.tokenize("echo \\\\ hello"), [
                StringToken(0, "echo"),
                WhitespaceToken(1),
                StringToken(2, "\\\\"),
                WhitespaceToken(3),
                StringToken(4, "hello")
            ]
        )

    def test_quoted_escaped_bslash(self):
        t = StringToken(2, "", quote="'", features=self.parser.features)
        t.text = "\\"
        tokens = self.parser.tokenize("echo '\\\\'")
        #self.parser.clean_escapes(tokens)
        assert_equal(
            tokens, [
                StringToken(0, "echo"),
                WhitespaceToken(1),
                t
            ]
        )

    def test_escaped_operators(self):
        for op in OPERATORS:
            yield self._test_escaped_operator, op

    def _test_escaped_operator(self, op):
        assert_equal(
            self.parser.tokenize("echo \\" + '\\'.join(op)), [
                StringToken(0, "echo"),
                WhitespaceToken(1),
                StringToken(2, op)
            ]
        )

    def test_quoted_operators(self):
        for quote in ("'", "\""):
            for op in OPERATORS:
                yield self._test_quoted_operator, quote, op

    def _test_quoted_operator(self, quote, op):
        assert_equal(
            self.parser.tokenize("echo {}{}{}".format(quote, op, quote)), [
                StringToken(0, "echo"),
                WhitespaceToken(1),
                StringToken(2, op, quote=quote)
            ]
        )

    def test_operators_surround_spaces(self):
        for op in OPERATORS:
            yield self._test_operator_surround_spaces, op

    def _test_operator_surround_spaces(self, op):
        assert_equal(
            self.parser.tokenize("echo {} postfix".format(op)), [
                StringToken(0, 'echo'),
                WhitespaceToken(1),
                OperatorToken(2, op),
                WhitespaceToken(3),
                StringToken(4, "postfix")
            ]
        )

    def test_operators_leading_space(self):
        for op in OPERATORS:
            yield self._test_operator_leading_space, op

    def _test_operator_leading_space(self, op):
        assert_equal(
            self.parser.tokenize("echo {}postfix".format(op)), [
                StringToken(0, 'echo'),
                WhitespaceToken(1),
                OperatorToken(2, op),
                StringToken(3, "postfix")
            ]
        )

    def test_operators_trailing_space(self):
        for op in OPERATORS:
            yield self._test_operator_trailing_space, op

    def _test_operator_trailing_space(self, op):
        assert_equal(
            self.parser.tokenize("echo{} postfix".format(op)), [
                StringToken(0, 'echo'),
                OperatorToken(1, op),
                WhitespaceToken(2),
                StringToken(3, "postfix")
            ]
        )

    def test_operators_nospace(self):
        for op in OPERATORS:
            yield self._test_operator_nospace, op

    def _test_operator_nospace(self, op):
        assert_equal(
            self.parser.tokenize("echo{}postfix".format(op)), [
                StringToken(0, 'echo'),
                OperatorToken(1, op),
                StringToken(2, "postfix")
            ]
        )

    def test_qutoted_escape_normal_char(self):
        assert_equal(
            self.parser.tokenize("echo '\\c'"), [
                StringToken(0, "echo"),
                WhitespaceToken(1),
                StringToken(2, "\\c", quote="'")
            ]
        )

    def test_trailing_escape(self):
        self.parser.features.multiline = False
        t = StringToken(2, "\\")

        assert_equal(
            self.parser.tokenize("echo \\"), [
                StringToken(0, "echo"),
                WhitespaceToken(1),
                t
            ]
        )

    def test_trailing_escape_multiline(self):
        t = StringToken(2, "")
        t.text = "\\"

        assert_raises(
            TrailingEscapeError,
            self.parser.tokenize,
            "echo \\"
        )
