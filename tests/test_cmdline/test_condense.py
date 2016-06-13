from nose.tools import *
from pypsi.cmdline import *
from pypsi.features import BashFeatures

class TestCondense(object):

    def setUp(self):
        self.parser = StatementParser(features=BashFeatures())

    def test_whitespace(self):
        tokens = [
            StringToken(0, "echo"),
            WhitespaceToken(1),
            StringToken(2, "hello")
        ]
        assert_equal(self.parser.condense(tokens), [
            StringToken(0, "echo"),
            StringToken(1, "hello")
        ])

    def test_condense_strings(self):
        assert_equal(
            self.parser.condense([
                StringToken(0, "echo"),
                WhitespaceToken(1),
                StringToken(2, "hello"),
                StringToken(3, "world", quote="'")
            ]), [
                StringToken(0, "echo"),
                StringToken(2, "helloworld", quote="'"),
            ]
        )

    def test_condense_mixed_quotes(self):
        assert_equal(
            self.parser.condense([
                StringToken(0, "echo", quote="'"),
                StringToken(1, "hello"),
                StringToken(2, "world", quote="\"")
            ]),
            [StringToken(0, "echohelloworld", quote="\"")]
        )

    def test_all_whitespace(self):
        assert_equal(
            self.parser.condense([WhitespaceToken(0), WhitespaceToken(1)]),
            []
        )

    def test_operator(self):
        assert_equal(
            self.parser.condense([
                StringToken(0, "echo"),
                WhitespaceToken(1),
                StringToken(2, "hello world", quote="'"),
                WhitespaceToken(3),
                OperatorToken(4, ">"),
                WhitespaceToken(5),
                StringToken(6, "output.txt")
            ]), [
                StringToken(0, "echo"),
                StringToken(1, "hello world", quote="'"),
                OperatorToken(2, ">"),
                StringToken(3, "output.txt")
            ]
        )
