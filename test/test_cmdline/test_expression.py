import pytest
from pypsi.cmdline import *

class TestExpression(object):

    def test_empty(self):
        assert Expression.parse([]) == (None, None)

    def test_only_operand(self):
        assert Expression.parse(['x']) == (None, None)

    def test_no_value(self):
        assert Expression.parse(['x', '+']) == ([], Expression('x', '+', ''))

    def test_whitespace(self):
        assert Expression.parse(['   ', '  x', '-900']) == ([], Expression('x', '-', '900'))

    @pytest.mark.parametrize('args,expected', [
        [['xy', '+=', '9'], ['xy', '+=', '9']],
        [['xy+=', '9'], ['xy', '+=', '9']],
        [['xy', '+=9'], ['xy', '+=', '9']],
        [['xy+=9'], ['xy', '+=', '9']]
    ])
    def test_combination(self, args, expected):
        assert Expression.parse(args) == ([], Expression(*expected))
