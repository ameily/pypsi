
from pypsi.cmdline import *
from pypsi.features import BashFeatures
from nose.tools import *


class TestCmdlineBuild(object):

    def setUp(self):
        self.parser = StatementParser(features=BashFeatures())

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

    def test_redirect_stdout_append(self):
        assert_equal(
            self.parser.build([
                StringToken(0, "echo"),
                WhitespaceToken(1),
                StringToken(2, "hello"),
                OperatorToken(3, ">>"),
                StringToken(4, "output.txt")
            ]),
            Statement([
                CommandInvocation(
                    name="echo",
                    args=["hello"],
                    stdout=("output.txt", 'a')
                )
            ])
        )

    def test_redirect_stdin(self):
        assert_equal(
            self.parser.build([
                StringToken(0, "echo"),
                WhitespaceToken(1),
                StringToken(2, "hello"),
                OperatorToken(3, "<"),
                StringToken(4, "input.txt")
            ]),
            Statement([
                CommandInvocation(
                    name="echo",
                    args=["hello"],
                    stdin='input.txt'
                )
            ])
        )

    def test_redirect_stdin_stdout(self):
        assert_equal(
            self.parser.build([
                StringToken(0, "echo"),
                WhitespaceToken(1),
                StringToken(2, "hello"),
                OperatorToken(3, ">"),
                StringToken(4, "output.txt"),
                WhitespaceToken(5),
                OperatorToken(6, "<"),
                StringToken(7, "input.txt")
            ]),
            Statement([
                CommandInvocation(
                    name="echo",
                    args=["hello"],
                    stdout=("output.txt", 'w'),
                    stdin='input.txt'
                )
            ])
        )

    def test_chain_operators(self):
        for op in ('|', '&&', '||', ';'):
            yield self._test_chain_operator, op

    def _test_chain_operator(self, op):
        assert_equal(
            self.parser.build([
                StringToken(0, "echo"),
                WhitespaceToken(1),
                StringToken(2, "hello"),
                OperatorToken(3, op),
                WhitespaceToken(4),
                StringToken(5, "grep"),
                WhitespaceToken(6),
                StringToken(7, 'hell')
            ]),
            Statement([
                CommandInvocation(
                    name="echo",
                    args=["hello"],
                    chain=op
                ),
                CommandInvocation(
                    name="grep",
                    args=["hell"]
                )
            ])
        )

    def test_duplicate_redirects(self):
        for op in ('>', '>>', '<'):
            yield self._test_duplicate_redirect, op

    def _test_duplicate_redirect(self, op):
        assert_raises(
            StatementSyntaxError,
            self.parser.build, [
                StringToken(0, "echo"),
                WhitespaceToken(1),
                StringToken(2, "hello"),
                OperatorToken(3, op),
                StringToken(4, "first.txt"),
                OperatorToken(5, op),
                StringToken(6, "second.txt")
            ]
        )

    def test_trailing_operators(self):
        for op in ('|', '||', '&&', '>', '>>', '<'):
            yield self._test_trailing_operator, op

    def _test_trailing_operator(self, op):
        assert_raises(
            StatementSyntaxError,
            self.parser.build, [
                StringToken(0, "echo"),
                OperatorToken(1, op)
            ]
        )

    def test_trailing_semicolon(self):
        assert_equal(
            self.parser.build([
                StringToken(0, "echo"),
                WhitespaceToken(1),
                OperatorToken(2, ';')
            ]), Statement([
                CommandInvocation(
                    name="echo",
                    chain=";"
                )
            ])
        )

    def test_leading_operators(self):
        for op in ('|', '||', '&&', ';', '>', '>>', '<'):
            yield self._test_leading_operator, op

    def _test_leading_operator(self, op):
        assert_raises(
            StatementSyntaxError,
            self.parser.build, [
                OperatorToken(0, op),
                StringToken(1, "echo")
            ]
        )

    def test_duplicate_redirect_pipe(self):
        assert_raises(
            StatementSyntaxError,
            self.parser.build, [
                StringToken(0, "echo"),
                WhitespaceToken(1),
                OperatorToken(2, ">"),
                StringToken(3, "output.txt"),
                OperatorToken(4, '|'),
                StringToken(5, 'grep')
            ]
        )

    def test_duplicate_adjacent_operator(self):
        assert_raises(
            StatementSyntaxError,
            self.parser.build, [
                StringToken(0, "echo"),
                OperatorToken(1, ">"),
                OperatorToken(2, ">")
            ]
        )

    def test_unknown_operator(self):
        assert_raises(
            StatementSyntaxError,
            self.parser.build, [
                StringToken(0, "echo"),
                OperatorToken(1, "&")
            ]
        )
