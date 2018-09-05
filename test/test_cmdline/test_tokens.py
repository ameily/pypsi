
import pytest
from pypsi.cmdline import *


class TestTokens(object):

    @pytest.mark.parametrize('op', (';', '&&', '|', '||'))
    def test_operator_is_chain(self, op):
        token = OperatorToken(0, op)
        assert token.is_chain_operator() is True

    @pytest.mark.parametrize('op', ('>', '>>', '<'))
    def test_operator_is_not_chain(self, op):
        token = OperatorToken(0, op)
        assert token.is_chain_operator() is False
