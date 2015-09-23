
from nose.tools import *
from pypsi.cmdline import *


class TestCleanEscapes(object):

    def setUp(self):
        self.parser = StatementParser()

    def test_simple(self):
        tokens = [
            StringToken(0, "echo"),
            WhitespaceToken(1),
            StringToken(2, "hello")
        ]

        self.parser.clean_escapes(tokens)
        assert_equal(
            tokens, [
                StringToken(0, "echo"),
                WhitespaceToken(1),
                StringToken(2, "hello")
            ]
        )
