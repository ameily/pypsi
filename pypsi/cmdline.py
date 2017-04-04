#
# Copyright (c) 2015, Adam Meily <meily.adam@gmail.com>
# Pypsi - https://github.com/ameily/pypsi
#
# Permission to use, copy, modify, and/or distribute this software for any
# purpose with or without fee is hereby granted, provided that the above
# copyright notice and this permission notice appear in all copies.
#
# THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
# WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
# MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
# ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
# WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
# ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
# OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
#


'''
Classes used for parsing user input.
'''

import sys
from pypsi.utils import safe_open


__all__ = (
    'Token', 'StringToken', 'OperatorToken', 'WhitespaceToken',
    'IORedirectionError', 'StatementParser', 'StatementSyntaxError',
    'CommandNotFoundError', 'CommandInvocation', 'Expression', 'Statement',
    'TrailingEscapeError'
)


#: The token accepts more characters.
TokenContinue = 0

#: The token does not accept the current chracter.
TokenEnd = 1

#: The token is finished and the current chracter should not be processed
#: again.
TokenTerm = 2


class Token(object):
    '''
    Base class for all tokens.
    '''

    def __init__(self, index, features=None):
        '''
        :param int index: the starting index of this token
        '''
        self.index = index
        self.features = None


class WhitespaceToken(Token):
    '''
    Whitespace token that can contain any number of whitespace characters.
    '''

    def __init__(self, index, c=' ', features=None):
        super(WhitespaceToken, self).__init__(index, features)
        self.text = c

    def add_char(self, c):
        '''
        Add a character to this token.

        :param str c: the current character
        :returns int: TokenEnd or TokenContinue
        '''
        if c in (' ', '\t', '\xa0'):
            self.text += c
            return TokenContinue
        else:
            return TokenEnd

    def __str__(self):
        return "WhitespaceToken( {} )".format(self.text)

    def __eq__(self, other):
        return isinstance(other, WhitespaceToken)


class StringToken(Token):
    '''
    A string token. This token may be bound by matching quotes and/or contain
    escaped whitespace characters.
    '''

    def __init__(self, index, c, quote=None, features=None):
        '''
        :param str c: the current string or character
        :param str quote: the surrounding quotes, `None` if there isn't any
        '''
        super(StringToken, self).__init__(index, features)
        self.quote = quote
        self._escape_char = features.escape_char if features else ''
        self.escape = False
        self.text = ''
        self.open_quote = False

        if c in ('"', "'"):
            self.quote = c
            self.open_quote = True
        elif self._escape_char and c == self._escape_char:
            self.escape = True
        elif c:
            self.text += c

    def add_char(self, c):
        '''
        Add a character to this token.

        :param str c: the current character
        :returns int: TokenEnd or TokenContinue
        '''
        ret = TokenContinue
        if self.escape:
            self.escape = False
            if self.quote:
                if c == self.quote:
                    self.text += c
                elif c is self._escape_char:
                    self.text += self._escape_char + self._escape_char
                else:
                    self.text += self._escape_char
                    self.text += c
            elif c in (' ', '\t', "'", "\"") or c in OperatorToken.Operators:
                self.text += c
            else:
                self.text += self._escape_char
                self.text += c
        elif self.quote:
            if c == self.quote:
                ret = TokenTerm
                self.open_quote = False
            elif c == self._escape_char:
                self.escape = True
            else:
                self.text += c
        else:
            if c == self._escape_char:
                self.escape = True
            elif c in (' ', '\t', ';', '|', '&', '>', '<', '\xa0'):
                ret = TokenEnd
            elif c in ('"', "'"):
                ret = TokenEnd
            else:
                self.text += c

        return ret

    def combine_token(self, token):
        self.text += token.text
        self.open_quote = token.open_quote
        self.escape = token.escape
        self.quote = token.quote

    def __str__(self):
        return "String( {quote}{text}{quote}, {open_quote}, {escape} )".format(
            quote=self.quote or '',
            text=self.text,
            open_quote=self.open_quote,
            escape=self.escape
        )

    def __eq__(self, other):
        return (
            isinstance(other, StringToken) and
            self.quote == other.quote and
            self.text == other.text and
            self.open_quote == other.open_quote and
            self.escape == other.escape
        )


class OperatorToken(Token):
    '''
    An operator token. An operator can consist of one or more repetitions of
    the same operator character. For example, the string ">>" would be parsed
    as one `OperatorToken`, whereas the string "<>" would be parsed as two
    separate `OperatorToken` objects.
    '''

    #: Valid operator characters
    Operators = '<>|&;'

    def __init__(self, index, operator):
        '''
        :param str operator: the operator
        '''
        super(OperatorToken, self).__init__(index)
        self.operator = operator

    def add_char(self, c):
        '''
        Add a character to this token.

        :param str c: the current character
        :returns int: TokenEnd or TokenContinue
        '''
        if c == self.operator[0]:
            self.operator += c
            return TokenContinue
        return TokenEnd

    def __str__(self):
        return "OperatorToken( {} )".format(self.operator)

    def is_chain_operator(self):
        for c in self.operator:
            if c in ('>', '<'):
                return False
        return True

    def __eq__(self, other):
        return (
            isinstance(other, OperatorToken) and
            self.operator == other.operator
        )


class IORedirectionError(Exception):

    def __init__(self, path, message):
        self.path = path
        self.message = message

    def __str__(self):
        return "{}: {}".format(self.path, self.message)


class CommandNotFoundError(Exception):
    '''
    The specified command does not exist.
    '''

    def __init__(self, name):
        #: the command name
        self.name = name

    def __str__(self):
        return self.name + ": command not found"


class Statement(object):
    '''
    A parsed statement containing a list of :class:`CommandInvocation`
    instances.
    '''

    def __init__(self, invokes=None):
        '''
        :param list[CommandInvocation] invokes: list of command invocations
        '''
        self.invokes = invokes or []

    def append(self, invoke):
        '''
        Append a new command invocation.

        :param CommandInvocation invoke: parsed command invocation
        '''
        self.invokes.append(invoke)

    def __iter__(self):
        '''
        :returns: an iterator for the :class:`CommandInvocation` instances
        '''
        return iter(self.invokes)

    def __nonzero__(self):
        '''
        :returns bool: :const:`True` if there is at least 1 parsed command
            invocation, :const:`False` otherwise
        '''
        return len(self.invokes) > 0

    def __len__(self):
        '''
        :returns int: the number of command invocations
        '''
        return len(self.invokes)

    def __eq__(self, other):
        return isinstance(other, Statement) and self.invokes == other.invokes


class CommandInvocation(object):
    '''
    An invocation of a command.
    '''

    def __init__(self, name, args=None, stdout=None, stderr=None, stdin=None,
                 chain=None):
        #: Command name
        self.name = name
        #: List of command arguments
        self.args = args or []
        #: stdout redirection
        self.stdout = stdout
        #: stderr redirection
        self.stderr = stderr
        #: stderr redirection
        self.stdin = stdin
        #: The chain operator, if any is specified: &&, ||, |, ;.
        self.chain = chain
        #: The resolved pypsi command (:class:`~pypsi.core.Command`)
        self.cmd = None
        #: The fallback command to use if :attr:`cmd` is :const:`None`.
        self.fallback_cmd = None

    def __eq__(self, other):
        return (
            isinstance(other, CommandInvocation) and
            self.name == other.name and
            self.args == other.args and
            self.stdout == other.stdout and
            self.stderr == other.stderr and
            self.stdin == other.stdin and
            self.chain == other.chain and
            self.cmd == other.cmd and
            self.fallback_cmd == other.fallback_cmd
        )

    def __str__(self):
        s = "{name} {args}".format(self.name, ' '.join(self.args))
        if self.stdout:
            if isinstance(self.stdout, tuple) and self.stdout[1] == 'a':
                s += " >> " + self.stdout[0]
            else:
                s += " > " + self.stdout

        if self.stdin:
            s += " < " + self.stdin

        if self.chain:
            s += " " + self.chain

        return s

    def setup(self, shell):
        '''
        Retrieve the Pypsi command to execute and setup the streams for stdout,
        stderr, and stdin depending on whether I/O redirection is being
        performed.

        :raises CommandNotFoundError: command specified does not exist
        :raises IORedirectionError: I/O redirection error occurred
        '''

        if self.name in shell.commands:
            self.cmd = shell.commands[self.name]
        elif shell.fallback_cmd:
            self.fallback_cmd = shell.fallback_cmd
        else:
            raise CommandNotFoundError(self.name)

        try:
            self.stdout = self.get_output(self.stdout)
            self.stderr = self.get_output(self.stdout)
            self.stdin = self.get_input(self.stdin)
        except:
            self.close_streams()
            raise

    def get_output(self, output):
        '''
        Open an output stream, if specified.

        :returns file: the stream opened for writting if specified, otherwise
            const:`None`.
        '''

        if isinstance(output, tuple):
            # output is a tuple of (path, mode)
            path, mode = output
            ret = self.get_stream(path, mode)
        elif isinstance(output, str):
            # output is a path
            ret = self.get_stream(output, 'w')
        else:
            # output is either None or an existing open stream
            ret = output
        return ret

    def get_input(self, stream):
        '''
        Open an input stream, if specified.

        :returns file: the stream opened for reading if specified, otherwise
            :const:`None`.
        '''

        if isinstance(stream, str):
            ret = self.get_stream(stream, 'r', safe=True)
        else:
            ret = stream
        return ret

    def get_stream(self, path, mode, safe=False):
        '''
        Open a file path.

        :param str path: file path
        :param str mode: file open mode
        :param bool safe: whether to use :meth:`pypsi.util.safe_open` instead
            of the standard :meth:`open` method.

        :raises IORedirectionError: stream could not be opened
        '''

        func = safe_open if safe else open
        try:
            fp = func(path, mode=mode)
        except OSError as e:
            raise IORedirectionError(path, e.strerror)
        except Exception as e:
            raise IORedirectionError(path, str(e))
        else:
            return fp

    def close_streams(self):
        '''
        Close all streams that were opened.
        '''

        for fp in (self.stdout, self.stderr, self.stdin):
            if fp and hasattr(fp, 'close') and not fp.closed:
                fp.close()

    def setup_io(self):
        '''
        Setup stdout, stderr, and stdin by proxying the thread local streams.
        '''

        if self.stdout:
            sys.stdout._proxy(self.stdout)
        if self.stderr:
            sys.stderr._proxy(self.stderr)
        if self.stdin:
            sys.stdin._proxy(self.stdin)

    def cleanup_io(self):
        '''
        Close proxied streams and unproxy them.
        '''

        self.close_streams()

        if self.stdout:
            sys.stdout._unproxy()
        if self.stderr:
            sys.stderr._unproxy()
        if self.stdin:
            sys.stdin._unproxy()

    def chain_and(self):
        '''
        :returns: :const:`True` if the chain operator is AND (&&)
        '''

        return self.chain == '&&'

    def chain_or(self):
        '''
        :returns: :const:`True` if the chain operator is OR (||)
        '''

        return self.chain == '||'

    def chain_uncond(self):
        '''
        :returns: :const:`True` if the chain operator is UNCONDITIONAL (;)
        '''

        return self.chain == ';'

    def chain_pipe(self):
        '''
        :returns: :const:`True` if the chain operator is PIPE (|)
        '''

        return self.chain == '|'

    def __call__(self, shell):
        '''
        Invoke the command by proxying streams, running the command, and
        cleaning the resetting streams.

        :returns: the commnd's return code.
        '''

        self.setup_io()
        try:
            if self.fallback_cmd:
                rc = self.fallback_cmd.fallback(shell, self.name, self.args)
            else:
                rc = self.cmd.run(shell, self.args)
        finally:
            self.cleanup_io()
        return rc

    def should_continue(self, prev_rc):
        '''
        :returns: whether this invocation is chained and, using the previous
            invocation's return code, determine if the next command in the
            chain should be executed.
        '''

        return (
            not self.chain or (
                self.chain_uncond() or
                (self.chain_or() and prev_rc is not 0) or
                (self.chain_and() and prev_rc is 0)
            )
        )


class StatementSyntaxError(SyntaxError):
    '''
    Invalid statement syntax was entered.
    '''

    def __init__(self, message, index):
        '''
        :param str message: error message
        :param int index: index in the statement that caused the error
        '''
        self.message = message
        self.index = index

    def __str__(self):
        return "syntax error at {}: {}".format(self.index, self.message)


class UnclosedQuotationError(StatementSyntaxError):
    '''
    The final token contains an unclosed quotation.
    '''

    def __init__(self, index):
        super(UnclosedQuotationError, self).__init__("unclosed quotation",
                                                     index)


class TrailingEscapeError(StatementSyntaxError):
    '''
    The final token ends with an escape character.
    '''

    def __init__(self, index):
        super(TrailingEscapeError, self).__init__("trailing escape character",
                                                  index)


class StatementParser(object):
    '''
    Parses raw user input into a :class:`Statement`.
    '''

    def __init__(self, features=None):
        self.features = features
        self.tokens = []
        self.token = None

    def process(self, index, c):
        '''
        Process a single character of input.

        :param int index: current character index
        :param str c: current character
        '''

        if self.token:
            action = self.token.add_char(c)
            if action == TokenEnd:
                self.tokens.append(self.token)
                self.token = None
                self.process(index, c)
            elif action == TokenTerm:
                self.tokens.append(self.token)
                self.token = None
            else:
                pass
        else:
            if c in (' ', '\t', '\xa0'):
                self.token = WhitespaceToken(index)
            elif c in ('>', '<', '|', '&', ';'):
                self.token = OperatorToken(index, c)
            else:
                self.token = StringToken(index, c, features=self.features)

    def tokenize(self, line):
        '''
        Transform a `str` into a `list` of :class:`Token` objects.

        :param str line: the line of text to tokenize
        :returns: `list` of :class:`Token` objects
        '''
        index = 0
        for c in line:
            self.process(index, c)
            index += 1

        if self.token and self.features:
            if isinstance(self.token, StringToken):
                if self.token.escape:
                    if self.features and self.features.multiline:
                        # The last character in the input was an escape and the
                        # shell supports multiline input. Switch back to the
                        # shell to allow further input.
                        raise TrailingEscapeError(self.token.index)
                    elif self.features:
                        self.token.text += self.features.escape_char
                        self.token.escape = False
                elif self.token.open_quote:
                    if self.features and self.features.multiline:
                        # The last token is an unclosed quotation and the shell
                        # supports multiline line input. Switch back to the
                        # shell to allow further input.
                        #
                        # We add a newline to the last text token since we are
                        # in a quoted string.
                        self.token.text += '\n'
                        raise UnclosedQuotationError(self.token.index)

            self.tokens.append(self.token)
        elif self.token:
            self.tokens.append(self.token)

        return self.tokens

    def clean_escapes(self, tokens):
        '''
        Remove all escape sequences.

        :param list tokens: :class:`Token` objects to remove escape sequences
        '''
        escape_char = self.features.escape_char if self.features else ''
        for token in tokens:
            if not isinstance(token, StringToken) or (
                    escape_char not in token.text or token.quote):
                continue

            text = ''
            escape = False
            for c in token.text:
                if escape:
                    text += c
                    escape = False
                elif c == escape_char:
                    escape = True
                else:
                    text += c

            if escape:
                text += escape_char

            token.text = text

    def condense(self, tokens):
        '''
        Condenses sequential like :class:`Token` objects into a single
        :class:`Token` of the same type. For example, two sequential
        :class:`StringToken` objects will be concatenated into a single
        :class:`StringToken`.

        :param list tokens: :class:`Token` objects to condense
        :returns: condensed `list` of :class:`Token` objects
        '''

        prev = None
        condensed = []
        for token in tokens:
            if isinstance(token, StringToken):
                if (token.quote and self.features and
                        self.features.preserve_quotes):
                    token.text = "{q}{t}{q}".format(q=token.quote,
                                                    t=token.text)

                if isinstance(prev, StringToken):
                    prev.combine_token(token)
                    token = prev
                else:
                    condensed.append(token)
            elif not isinstance(token, WhitespaceToken):
                condensed.append(token)
            prev = token

        return condensed

    def build(self, tokens):
        '''
        Create a :class:`Statement` object from tokenized input and statement
        context. This method will first remove all remaining escape sequences
        and then :meth:`condense` all the tokens before building the statement.

        :param list tokens: list of :class:`Token` objects to process as a
            statement
        :raises: :class:`StatementSyntaxError` on error
        :returns: (:class:`Statement`) the parsed statement
        '''

        statement = Statement()
        cmd = None
        prev = None
        self.clean_escapes(tokens)
        tokens = self.condense(tokens)

        for token in tokens:
            if cmd:
                if isinstance(prev, OperatorToken) and (
                        prev.operator in ('>', '<', '>>')):
                    if isinstance(token, StringToken):
                        if prev.operator in ('>', '>>'):
                            cmd.stdout = (
                                token.text,
                                'w' if prev.operator == '>' else 'a'
                            )
                        elif prev.operator == '<':
                            cmd.stdin = token.text
                    else:
                        raise StatementSyntaxError(
                            message="unexpected token: {}".format(str(token)),
                            index=token.index
                        )
                elif isinstance(token, StringToken):
                    cmd.args.append(token.text)
                elif isinstance(token, OperatorToken):
                    done = False
                    if token.operator in ('||', '&&', ';'):
                        cmd.chain = token.operator
                        done = True
                    elif token.operator == '|':
                        if cmd.stdout:
                            msg = ("unexpected token: {}: duplicate output "
                                   "redirection is invalid").format(str(token))
                            raise StatementSyntaxError(
                                message=msg,
                                index=token.index
                            )

                        cmd.chain = '|'
                        done = True
                    elif token.operator in ('>', '>>'):
                        if cmd.stdout:
                            msg = ("unexpected token: {}: duplicate output "
                                   "redirection is invalid").format(str(token))
                            raise StatementSyntaxError(
                                message=msg,
                                index=token.index
                            )
                    elif token.operator == '<':
                        if cmd.stdin or (len(statement) > 1 and
                                         statement[-1].chain == '|'):
                            # The previous command in was a pipe, so input
                            # redirection is not supported.
                            msg = ("unexpected token: {} duplicate input "
                                   "redirection is invalid").format(str(token))
                            raise StatementSyntaxError(
                                message=msg,
                                index=token.index
                            )
                    else:
                        raise StatementSyntaxError(
                            message="unknown operator: " + token.operator,
                            index=token.index
                        )

                    if done:
                        statement.append(cmd)
                        cmd = None
            else:
                if isinstance(token, StringToken):
                    cmd = CommandInvocation(token.text)
                elif not isinstance(token, WhitespaceToken):
                    raise StatementSyntaxError(
                        message="unexpected token: {}".format(str(token)),
                        index=token.index
                    )
            prev = token

        if isinstance(prev, StringToken) or (
                isinstance(prev, OperatorToken) and prev.operator == ';'):
            pass
        elif prev:
            raise StatementSyntaxError(
                message="unexpected token: {}".format(str(prev)),
                index=prev.index
            )

        if cmd:
            statement.append(cmd)

        return statement


class Expression(object):
    '''
    Holds a string-based expression in the form of ``operand operator value``.
    This class makes parsing expressions that may be in a single string or a
    list of strings. For example, the :class:`pypsi.plugins.VarCommand` command
    accepts input in the form of: ``name = value``. This class allows for the
    user to input any of the following lines and the same Expression object
    would be created, regardless of how the input lines are tokenized:

    - ``some_var = 2`` => ``['some_var', '=', '2']``
    - ``some_var= 2`` => ``['some_var=', '2']``
    - ``some_var =2`` => ``['some_var', '=2']``
    - ``some_var=2`` => ``['some_var=2']``
    '''

    Operators = '-+=/*'
    Whitespace = ' \t'

    def __init__(self, operand, operator, value):
        self.operand = operand
        self.operator = operator
        self.value = value

    def __str__(self):
        return "{} {} {}".format(self.operand, self.operator, self.value)

    def __eq__(self, other):
        return (
            isinstance(other, Expression) and
            self.operand == other.operand and
            self.operator == other.operator and
            self.value == other.value
        )

    @classmethod
    def parse(cls, args):
        '''
        Create an Expression from a list of strings.

        :param list args: arguments
        :returns: a tuple of ``(remaining, expression)``, where ``remaining``
            is the list of remaining string arguments of ``args`` after parsing
            has completed, and ``expression`` in the parsed
            :class:`Expression`, or :const:`None` if the expression is invalid.
        '''
        state = 'operand'
        operand = operator = value = None
        done = False
        remaining = list(args)
        for arg in args:
            for c in arg:
                if state == 'operand':
                    if c in Expression.Whitespace:
                        if operand:
                            state = 'operator'
                    elif c in Expression.Operators:
                        state = 'operator'
                        operator = c
                    else:
                        if operand is None:
                            operand = c
                        else:
                            operand += c
                elif state == 'operator':
                    if c in Expression.Operators:
                        if operator is None:
                            operator = c
                        else:
                            operator += c
                    elif c in Expression.Whitespace:
                        if operator:
                            state = 'value'
                            done = True
                            value = ''
                    else:
                        state = 'value'
                        value = c
                        done = True
                elif state == 'value':
                    if c in Expression.Whitespace and not value:
                        pass
                    else:
                        value += c
            remaining.pop(0)
            if done:
                break

        if operator and not value:
            value = ''
        elif not done:
            return (None, None)

        return (remaining, Expression(operand, operator, value))
