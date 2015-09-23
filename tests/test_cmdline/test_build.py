
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
                StringToken(1, "hello")
            ]),
            Statement([
                CommandInvocation(
                    name="echo",
                    args=["hello"]
                )
            ])
        )
