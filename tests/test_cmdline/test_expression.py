
from pypsi.cmdline import *
from nose.tools import *

class TestExpression(object):

    def test_empty(self):
        assert_equal(
            Expression.parse([]),
            (None, None)
        )

    def test_only_operand(self):
        assert_equal(
            Expression.parse(['x']),
            (None, None)
        )

    def test_no_value(self):
        assert_equal(
            Expression.parse(['x', '+']),
            ([], Expression('x', '+', ''))
        )

    def test_whitespace(self):
        assert_equal(
            Expression.parse(['   ', '  x', '-900']),
            ([], Expression('x', '-', '900'))
        )

    def test_combinations(self):
        for args in [['xy', '+=', '9'], ['xy+=', '9'], ['xy', '+=9'], ['xy+=9']]:
            yield self._test_combination, args, ['xy', '+=', '9']

    def _test_combination(self, args, expected):
        assert_equal(
            Expression.parse(args),
            ([], Expression(*expected))
        )
