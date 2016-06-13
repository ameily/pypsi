
from nose.tools import *
from pypsi.cmdline import *
from pypsi.features import BashFeatures

def copy_tokens(tokens):
    result = []
    for token in tokens:
        if isinstance(token, StringToken):
            t = StringToken(token.index, token.text, token.quote)
            t.escape = token.escape
            result.append(t)
        elif isinstance(token, WhitespaceToken):
            result.append(WhitespaceToken(token.index))
        elif isinstance(token, OperatorToken):
            result.append(OperatorToken(token.operator))
        else:
            pass
    return result, tokens


class TestCleanEscapes(object):

    def setUp(self):
        self.parser = StatementParser(features=BashFeatures())

    def test_simple(self):
        t1, t2 = copy_tokens([
            StringToken(0, "echo"),
            WhitespaceToken(1),
            StringToken(2, "hello")
        ])

        self.parser.clean_escapes(t1)
        assert_equal(t1, t2)

    def test_quoted_escape(self):
        t1, t2 = copy_tokens([StringToken(0, "echo\\hello", quote="'")])
        self.parser.clean_escapes(t1)
        assert_equal(t1, t2)

    def test_escape_normal_char(self):
        t1 = [StringToken(0, "echo\\hello")]
        self.parser.clean_escapes(t1)
        assert_equal(t1, [StringToken(0, "echohello")])

    def test_double_escape(self):
        t1 = [StringToken(0, "echo\\\\hello")]
        self.parser.clean_escapes(t1)
        assert_equal(t1, [StringToken(0, "echo\\hello")])
