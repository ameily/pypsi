
from nose.tools import *
from pypsi.cmdline import *


class TestTokens(object):

    def test_string_token_str(self):
        x = str(StringToken(0, "hello world", quote="'"))

    def test_whitespace_token_str(self):
        x = str(WhitespaceToken(0))

    def test_operator_str(self):
        x = str(OperatorToken(0, ">"))

    def test_operator_is_chain(self):
        for op in (';', '&&', '|', '||'):
            yield self._test_operator_is_chain, op

    def _test_operator_is_chain(self, op):
        token = OperatorToken(0, op)
        assert_true(token.is_chain_operator())

    def test_operator_is_not_chain(self):
        token = OperatorToken(0, ">>")
        assert_false(token.is_chain_operator())
