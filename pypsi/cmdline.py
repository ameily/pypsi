#
# Copyright (c) 2014, Adam Meily
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without modification,
# are permitted provided that the following conditions are met:
#
# * Redistributions of source code must retain the above copyright notice, this
#   list of conditions and the following disclaimer.
#
# * Redistributions in binary form must reproduce the above copyright notice, this
#   list of conditions and the following disclaimer in the documentation and/or
#   other materials provided with the distribution.
#
# * Neither the name of the {organization} nor the names of its
#   contributors may be used to endorse or promote products derived from
#   this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR
# ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON
# ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#

'''
Classes used for parsing user input.
'''

import sys
from io import StringIO


TokenContinue = 0
'''The token accepts more characters.'''

TokenEnd = 1
'''The token does not accept the current character.'''

TokenTerm = 2
'''The token is finished and the current character should not be processed again.'''


class Token(object):
    '''
    Base class for all tokens.
    '''

    def __init__(self, index):
        '''
        :param int index: the starting index of this token
        '''
        self.index = index


class WhitespaceToken(Token):
    '''
    Whitespace token that can contain any number of whitespace characters.
    '''

    def __init__(self, index):
        super(WhitespaceToken, self).__init__(index)

    def add_char(self, c):
        '''
        Add a character to this token.

        :param str c: the current character
        :returns int: TokenEnd or TokenContinue
        '''
        if c in (' ', '\t','\xa0'):
            return TokenContinue
        return TokenEnd

    def __str__(self):
        return "WhitespaceToken()"


class StringToken(Token):
    '''
    A string token. This token may be bound by matching quotes and/or contain
    escaped whitespace characters.
    '''

    def __init__(self, index, c, quote=None):
        '''
        :param str c: the current string or character
        :param str quote: the surrounding quotes, `None` if there isn't any
        '''
        super(StringToken, self).__init__(index)
        self.quote = quote
        self.escape = False
        self.text = ''
        self.open_quote = False

        if c in ('"', "'"):
            self.quote = c
            self.open_quote = True
        elif c == '\\':
            self.escape = True
        else:
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
                elif c == '\\':
                    self.text += '\\'
                else:
                    self.text += '\\'
                    self.text += c
            elif c in (' ', '\t') or c in OperatorToken.Operators:
                self.text += c
            else:
                self.text += '\\'
                self.text += c
        elif self.quote:
            if c == self.quote:
                ret = TokenTerm
                self.open_quote = False
            elif c == '\\':
                self.escape = True
            else:
                self.text += c
        else:
            if c == '\\':
                self.escape = True
            elif c in (' ', '\t', ';', '|', '&', '>', '<','\xa0'):
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
        return "String( {quote}{text}{quote} )".format(
            quote=self.quote or '',
            text=self.text
        )

class OperatorToken(Token):
    '''
    An operator token. An operator can consist of one or more repetitions of the
    same operator character. For example, the string ">>" would be parsed as one
    `OperatorToken`, whereas the string "<>" would be parsed as two separate
    `OperatorToken` objects.
    '''

    Operators = '<>|&;'
    '''
    Valid operator characters.
    '''

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
        if c == self.operator:
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


class Statement(object):
    '''
    A parsed statement to be executed. A statement may contain the following:

    - Commands and arguments
    - I/O redirections
    - Command chaining

    Command chaining describes how multiple commands are executed sequentially.
    The chain operators can be one of the following:

    - **|** (pipe) - pass previous `stdout` to current `stdin` and stop the
      statement execution if a command fails
    - **||** (or) - only run the subsequent commands if the current command
      fails
    - **&&** (and) - only run subsequent commands if the current command
      succeeds
    - **;** (chain) - execute subsequent commands regardless of result

    Commands are considered to succeed if they return 0 and fail if they don't.
    See :meth:`pypsi.base.Command.run` for a more detailed description of
    command return codes.
    '''

    def __init__(self, ctx):
        '''
        :param StatementContext ctx: the current statement context
        '''
        #:current :class:`StatementContext` for this statement
        self.ctx = ctx

        #:`list` of :class:`CommandParams` describing the commands
        self.cmds = []

        #:`list` of chaining operators, `str`
        self.ops = []
        self.index = -1

    def __len__(self):
        '''
        :returns int: the number of commands in this statement
        '''
        return len(self.cmds)

    def __iter__(self):
        '''
        :returns iter: an iterator for :attr:`cmds`
        '''
        return iter(self.cmds)

    @property
    def cmd(self):
        '''
        (:class:`CommandParams`) the current command
        '''
        return self.cmds[self.index] if self.index < len(self.cmds) else None

    @property
    def op(self):
        '''
        (:class:`str`) the current chaining operator
        '''
        return self.ops[self.index] if self.index < len(self.ops) else None

    def next(self):
        '''
        Begin processing of the next command.

        :returns tuple: a `tuple` of :class:`CommandParams` and operator (`str`)
            defining the next command, and `(None, None)` if there are no more
            commands to execute
        '''
        self.index += 1
        return (
            self.cmds[self.index] if self.index < len(self.cmds) else None,
            self.ops[self.index] if self.index < len(self.ops) else None
        )


class IoRedirectionError(Exception):

    def __init__(self, path, message):
        self.path = path
        self.message = message


class StatementContext(object):
    '''
    Holds information about the current context of a statement. This class wraps
    the handling of I/O redirection and piping by setting the system streams
    to their appropriate values for a given command, and resetting them once the
    statement has finished executing.
    '''

    def __init__(self):
        self.prev = None
        self.pipe = None
        self.width = None

        self.stdout_state = sys.stdout.get_state()
        self.stderr_state = sys.stderr.get_state()

        #: the :data:`sys.stdin` when the statement context was created
        self.backup_stdin = sys.stdin

        #:(:class:`file`) the current `stdout` file object
        self.stdout = sys.stdout

        #:(:class:`file`) the current `stderr` file object
        self.stderr = sys.stderr

        #:(:class:`file`) the current `stdin` file objects
        self.stdin = sys.stdin

    def fork(self):
        '''
        Fork the context. This allows the new :class:`StatementContext` to run
        child commands under this context.

        :returns: (:class:`StatementContext`) the forked context
        '''
        ctx = StatementContext()
        ctx.stdin = ctx.backup_stdin = self.stdin
        #ctx.stdout = ctx.backup_stdout = self.stdout
        #ctx.stderr = ctx.backup_stderr = self.stderr
        ctx.prev = None
        ctx.pipe = self.pipe
        return ctx

    def setup_io(self, cmd, params, op):
        '''
        Setup the system streams to the correct file streams for the provided
        command parameters.

        :param pypsi.base.Command cmd: the current command
        :param CommandParams params: the command parameters
        :param str op: the current chaining operator
        :returns: 0 on success, -1 on error
        '''
        prev_pipe = self.prev and self.prev[1] == '|'
        if params.stdin_path:
            # Setup stdin if redirecting from a file
            try:
                sys.stdin = self.stdin = open(params.stdin_path, 'r')
            except OSError as e:
                raise IoRedirectionError(params.stdin_path, str(e))
        elif prev_pipe:
            # Previous command's stdout needs to be piped to current command's
            # stdin
            sys.stdout.flush()
            sys.stdout.seek(0)
            self.stdin = sys.stdin = self.stdout.stream
        else:
            # Reset stdin
            self.stdin = sys.stdin = self.backup_stdin

        if params.stdout_path:
            # Setup stdout if redirecting to a file
            try:
                sys.stdout.redirect(open(params.stdout_path, params.stdout_mode))
            except OSError as e:
                raise IoRedirectionError(params.stdout_path, str(e))
        elif op == '|':
            # Next command is a pipe, redirect stdout to a buffer
            sys.stdout.redirect(StringIO())
        else:
            # Reset stdout
            sys.stdout.close(was_pipe=prev_pipe)

        if params.stderr_path:
            # Setup stderr if redirecting to a file
            try:
                sys.stderr.redirect(open(params.stderr_path, 'w'))
            except OSError as e:
                raise IoRedirectionError(params.stderr_path, str(e))
        else:
            # Reset stderr
            sys.stderr.close()

        self.prev = (cmd, op)

        return 0

    def reset_io(self):
        '''
        Resets the system streams to their original values. This should be
        called after a statement has finished executing.
        '''
        sys.stdout.reset(self.stdout_state)
        sys.stderr.reset(self.stderr_state)

        if self.stdin != self.backup_stdin:
            self.stdin.close()
            sys.stdin = self.stdin = self.backup_stdin

        return 0


class CommandParams(object):
    '''
    Wrapper around a called command's parameters and information.
    '''

    def __init__(self, name, args=None, stdout_path=None, stdout_mode='w',
                 stderr_path=None, stdin_path=None):
        #:(:class:`str`) name of the command
        self.name = name
        #:(:class:`list`) list of `str` arguments passed in by the user
        self.args = args or []
        #:(:class:`str`) path to `stdout` if redirecting to a file
        self.stdout_path = stdout_path
        #:(:class:`str`) mode to pass to `open()` when opening the `stdout` redirection file
        self.stdout_mode = stdout_mode
        #:(:class:`str`) path to `stderr` if redirecting to a file
        self.stderr_path = stderr_path
        #:(:class:`str`) path to `stdin` if redirecting from a file
        self.stdin_path = stdin_path


class StatementSyntaxError(Exception):
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


class StatementParser(object):
    '''
    Parses raw user input into a :class:`Statement`.
    '''

    def __init__(self):
        pass

    def reset(self):
        '''
        Reset parsing state.
        '''
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
            if c in (' ', '\t','\xa0'):
                self.token = WhitespaceToken(index)
            elif c in ('>', '<', '|', '&', ';'):
                self.token = OperatorToken(index, c)
            else:
                self.token = StringToken(index, c)

    def tokenize(self, line):
        '''
        Transform a `str` into a `list` of :class:`Token` objects.

        :param str line: the line of text to tokenize
        :returns: `list` of :class:`Token` objects
        '''
        self.reset()
        index = 0
        for c in line:
            self.process(index, c)
            index += 1

        if self.token:
            if isinstance(self.token, StringToken):
                if self.token.escape:
                    self.token.text += '\\'
            self.tokens.append(self.token)

        return self.tokens

    def clean_escapes(self, tokens):
        '''
        Remove all escape sequences.

        :param list tokens: :class:`Token` objects to remove escape sequences
        '''
        for token in tokens:
            if not isinstance(token, StringToken) or ('\\' not in token.text or token.quote):
                continue

            text = ''
            escape = False
            for c in token.text:
                if escape:
                    text += c
                    escape = False
                elif c == '\\':
                    escape = True
                else:
                    text += c

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
                if isinstance(prev, StringToken):
                    #prev.text += token.text
                    prev.combine_token(token)
                    token = prev
                else:
                    condensed.append(token)
            elif not isinstance(token, WhitespaceToken):
                condensed.append(token)
            prev = token

        return condensed

    def build(self, tokens, ctx):
        '''
        Create a :class:`Statement` object from tokenized input and statement
        context. This method will first remove all remaining escape sequences
        and then :meth:`condense` all the tokens before building the statement.

        :param list tokens: list of :class:`Token` objects to process as a
            statement
        :param pypsi.cmdline.StatementContext ctx: the current statement context to use
        :raises: :class:`StatementSyntaxError` on error
        :returns: (:class:`Statement`) the parsed statement
        '''

        statement = Statement(ctx)
        cmd = None
        prev = None
        self.clean_escapes(tokens)
        tokens = self.condense(tokens)

        for token in tokens:
            if cmd:
                if isinstance(prev, OperatorToken) and prev.operator in ('>', '<', '>>'):
                    if isinstance(token, StringToken):
                        if prev.operator in ('>', '>>'):
                            cmd.stdout_path = token.text
                        elif prev.operator == '<':
                            cmd.stdin_path = token.text
                    else:
                        raise StatementSyntaxError(
                            message="unexpected token: {}".format(str(token)),
                            index=token.index
                        )
                elif isinstance(token, StringToken):
                    cmd.args.append(token.text)
                elif isinstance(token, OperatorToken):
                    done = True
                    if token.operator == '||':
                        statement.ops.append('||')
                    elif token.operator == '&&':
                        statement.ops.append('&&')
                    elif token.operator == ';':
                        statement.ops.append(';')
                    elif token.operator == '|':
                        if cmd.stdout_path:
                            raise StatementSyntaxError(
                                message="unexpected token: {}".format(str(token)),
                                index=token.index
                            )

                        statement.ops.append('|')
                    elif token.operator in ('>', '>>'):
                        if cmd.stdout_path:
                            raise StatementSyntaxError(
                                message="unexpected token: {}".format(str(token)),
                                index=token.index
                            )

                        cmd.stdout_mode = 'w' if token.operator == '>' else 'a'
                        done = False
                    elif token.operator == '<':
                        if cmd.stdin_path:
                            raise StatementSyntaxError(
                                message="unexpected token: {}".format(str(token)),
                                index=token.index
                            )

                        if statement.ops and statement.ops[-1] == '|':
                            raise StatementSyntaxError(
                                message="unexpected token: {}".format(str(token)),
                                index=token.index
                            )

                        cmd.stdin_path = ''
                        done = False
                    else:
                        raise StatementSyntaxError(
                            message="unknown operator: {}".format(token.operator),
                            index=token.index
                        )

                    if done:
                        statement.cmds.append(cmd)
                        cmd = None
            else:
                if isinstance(token, StringToken):
                    cmd = CommandParams(token.text)
                elif not isinstance(token, WhitespaceToken):
                    raise StatementSyntaxError(
                        message="unexpected token: {}".format(str(token)),
                        index=token.index
                    )
            prev = token

        if isinstance(prev, StringToken) or (isinstance(prev, OperatorToken) and prev.operator == ';'):
            pass
        elif prev:
            raise StatementSyntaxError(
                message="unexpected token: {}".format(str(prev)),
                index=prev.index
            )

        if cmd:
            statement.cmds.append(cmd)

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

    @classmethod
    def parse(cls, args):
        '''
        Create an Expression from a list of strings.

        :param list args: arguments
        :returns: a tuple of ``(remaining, expression)``, where ``remaining`` is
            the list of remaining string arguments of ``args`` after parsing has
            completed, and ``expression`` in the parsed :class:`Expression`, or
            :const:`None` if the expression is invalid.
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
                        if value is None:
                            done = True
                            value = c
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

