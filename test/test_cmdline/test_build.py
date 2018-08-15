
import pytest
from pypsi.cmdline import *
from pypsi.features import BashFeatures


class TestCmdlineBuild:

    def setup(self):
        self.parser = StatementParser(features=BashFeatures())

    def test_simple(self):
        assert (
            self.parser.build([
                StringToken(0, "echo"),
                WhitespaceToken(1),
                StringToken(2, "hello")
            ]) == Statement([
                CommandInvocation(
                    name="echo",
                    args=["hello"]
                )
            ])
        )

    def test_redirect_stdout(self):
        assert (
            self.parser.build([
                StringToken(0, "echo"),
                WhitespaceToken(1),
                StringToken(2, "hello"),
                OperatorToken(3, ">"),
                StringToken(4, "output.txt")
            ]) == Statement([
                CommandInvocation(
                    name="echo",
                    args=["hello"],
                    stdout=("output.txt", 'w')
                )
            ])
        )

    def test_redirect_stdout_append(self):
        assert (
            self.parser.build([
                StringToken(0, "echo"),
                WhitespaceToken(1),
                StringToken(2, "hello"),
                OperatorToken(3, ">>"),
                StringToken(4, "output.txt")
            ]) == Statement([
                CommandInvocation(
                    name="echo",
                    args=["hello"],
                    stdout=("output.txt", 'a')
                )
            ])
        )

    def test_redirect_stdin(self):
        assert (
            self.parser.build([
                StringToken(0, "echo"),
                WhitespaceToken(1),
                StringToken(2, "hello"),
                OperatorToken(3, "<"),
                StringToken(4, "input.txt")
            ]) == Statement([
                CommandInvocation(
                    name="echo",
                    args=["hello"],
                    stdin='input.txt'
                )
            ])
        )

    def test_redirect_stdin_stdout(self):
        assert (
            self.parser.build([
                StringToken(0, "echo"),
                WhitespaceToken(1),
                StringToken(2, "hello"),
                OperatorToken(3, ">"),
                StringToken(4, "output.txt"),
                WhitespaceToken(5),
                OperatorToken(6, "<"),
                StringToken(7, "input.txt")
            ]) == Statement([
                CommandInvocation(
                    name="echo",
                    args=["hello"],
                    stdout=("output.txt", 'w'),
                    stdin='input.txt'
                )
            ])
        )

    @pytest.mark.parametrize('op', ('|', '&&', '||', ';'))
    def test_chain_operator(self, op):
        assert (
            self.parser.build([
                StringToken(0, "echo"),
                WhitespaceToken(1),
                StringToken(2, "hello"),
                OperatorToken(3, op),
                WhitespaceToken(4),
                StringToken(5, "grep"),
                WhitespaceToken(6),
                StringToken(7, 'hell')
            ]) == Statement([
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

    @pytest.mark.parametrize('op', ('>', '>>', '<'))
    def test_duplicate_redirect(self, op):
        with pytest.raises(StatementSyntaxError):
            self.parser.build([
                StringToken(0, "echo"),
                WhitespaceToken(1),
                StringToken(2, "hello"),
                OperatorToken(3, op),
                StringToken(4, "first.txt"),
                OperatorToken(5, op),
                StringToken(6, "second.txt")
            ])

    @pytest.mark.parametrize('op', ('|', '||', '&&', '>', '>>', '<'))
    def test_trailing_operator(self, op):
        with pytest.raises(StatementSyntaxError):
            self.parser.build([
                StringToken(0, "echo"),
                OperatorToken(1, op)
            ])

    def test_trailing_semicolon(self):
        assert (
            self.parser.build([
                StringToken(0, "echo"),
                WhitespaceToken(1),
                OperatorToken(2, ';')
            ]) == Statement([
                CommandInvocation(
                    name="echo",
                    chain=";"
                )
            ])
        )

    @pytest.mark.parametrize('op', ('|', '||', '&&', ';', '>', '>>', '<'))
    def test_leading_operator(self, op):
        with pytest.raises(StatementSyntaxError):
            self.parser.build([
                OperatorToken(0, op),
                StringToken(1, "echo")
            ])

    def test_duplicate_redirect_pipe(self):
        with pytest.raises(StatementSyntaxError):
            self.parser.build([
                StringToken(0, "echo"),
                WhitespaceToken(1),
                OperatorToken(2, ">"),
                StringToken(3, "output.txt"),
                OperatorToken(4, '|'),
                StringToken(5, 'grep')
            ])

    def test_duplicate_adjacent_operator(self):
        with pytest.raises(StatementSyntaxError):
            self.parser.build([
                StringToken(0, "echo"),
                OperatorToken(1, ">"),
                OperatorToken(2, ">")
            ])

    def test_unknown_operator(self):
        with pytest.raises(StatementSyntaxError):
            self.parser.build([
                StringToken(0, "echo"),
                OperatorToken(1, "&")
            ])
