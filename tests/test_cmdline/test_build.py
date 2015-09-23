
from pypsi.cmdline import *
from nose.tools import *


class TestCmdlineBuild(object):

    def setUp(self):
        self.parser = StatementParser()

    def test_simple(self):
        assert_equal(
            self.parser.build([
                StringToken(0, "echo"),
                WhitespaceToken(1),
                StringToken(2, "hello")
            ]),
            Statement([
                CommandInvocation(
                    name="echo",
                    args=["hello"]
                )
            ])
        )

    def test_redirect_stdout(self):
        assert_equal(
            self.parser.build([
                StringToken(0, "echo"),
                WhitespaceToken(1),
                StringToken(2, "hello"),
                OperatorToken(3, ">"),
                StringToken(4, "output.txt")
            ]),
            Statement([
                CommandInvocation(
                    name="echo",
                    args=["hello"],
                    stdout=("output.txt", 'w')
                )
            ])
        )
