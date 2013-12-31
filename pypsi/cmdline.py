
import sys
from io import StringIO


TokenContinue = 0   # keep going
TokenEnd = 1        # c ends token, process c again
TokenTerm = 2       # c terms token


class Token(object):

    def __init__(self, index):
        self.index = index


class WhitespaceToken(Token):

    def __init__(self, index):
        super(WhitespaceToken, self).__init__(index)

    def add_char(self, c):
        if c in (' ', '\t'):
            return TokenContinue
        return TokenEnd

    def __str__(self):
        return "WhitespaceToken()"


class StringToken(Token):

    def __init__(self, index, c, quote=None):
        super(StringToken, self).__init__(index)
        self.quote = quote
        self.escape = False
        self.text = ''

        if c in ('"', "'"):
            self.quote = c
        elif c == '\\':
            self.escape = True
        else:
            self.text += c

    def add_char(self, c):
        ret = TokenContinue
        if self.escape:
            self.escape = False
            if self.quote:
                if c == self.quote:
                    self.text += c
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
            elif c == '\\':
                self.escape = True
            else:
                self.text += c
        else:
            if c == '\\':
                self.escape = True
            elif c in (' ', '\t', ';', '|', '&', '>', '<'):
                ret = TokenEnd
            elif c in ('"', "'"):
                ret = TokenEnd
            else:
                self.text += c

        return ret

    def __str__(self):
        return "String( {quote}{text}{quote} )".format(
            quote=self.quote or '',
            text=self.text
        )

class OperatorToken(Token):
    Operators = '<>|&;'

    def __init__(self, index, operator):
        super(OperatorToken, self).__init__(index)
        self.operator = operator

    def add_char(self, c):
        if c == self.operator:
            self.operator += c
            return TokenContinue
        return TokenEnd

    def __str__(self):
        return "OperatorToken( {} )".format(self.operator)


class Statement(object):

    def __init__(self, ctx):
        self.ctx = ctx
        self.cmds = []
        self.ops = []
        self.index = -1

    def __len__(self):
        return len(self.cmds)

    def __iter__(self):
        return iter(self.cmds)

    @property
    def cmd(self):
        return self.cmds[self.index] if self.index < len(self.cmds) else None

    @property
    def op(self):
        return self.ops[self.index] if self.index < len(self.ops) else None

    def next(self):
        self.index += 1
        return (
            self.cmds[self.index] if self.index < len(self.cmds) else None,
            self.ops[self.index] if self.index < len(self.ops) else None
        )


class StatementContext(object):

    def __init__(self):
        self.prev = None
        self.pipe = None
        self.backup_stdout = sys.stdout
        self.backup_stderr = sys.stderr
        self.backup_stdin = sys.stdin

        self.stdout = sys.stdout
        self.stderr = sys.stderr
        self.stdin = sys.stdin

    def fork(self):
        ctx = StatementContext()
        ctx.stdin = ctx.backup_stdin = self.stdin
        ctx.stdout = ctx.backup_stdout = self.stdout
        ctx.stderr = ctx.backup_stderr = self.stderr
        ctx.prev = None
        ctx.pipe = self.pipe
        return ctx

    def setup_io(self, cmd, params, op):
        if params.stdin_path:
            sys.stdin = self.stdin = open(params.stdin_path, 'r')
        elif self.prev and self.prev[1] == '|':
            self.stdout.flush()
            self.stdout.seek(0)
            self.stdin = sys.stdin = self.stdout
        else:
            self.stdin = sys.stdin = self.backup_stdin

        if params.stdout_path:
            sys.stdout = self.stdout = open(params.stdout_path, params.stdout_mode)
        elif op == '|':
            sys.stdout = self.stdout = StringIO()
        else:
            self.stdout = sys.stdout = self.backup_stdout

        if params.stderr_path:
            sys.stderr = self.stderr = open(params.stderr_path, 'w')
        else:
            self.stderr = sys.stderr = self.backup_stderr

        self.prev = (cmd, op)

        return 0

    def reset_io(self):
        if self.stdout != self.backup_stdout:
            self.stdout.close()
            sys.stdout = self.stdout = self.backup_stdout

        if self.stderr != self.backup_stderr:
            sys.stderr = self.stderr = self.backup_stderr

        if self.stdin != self.backup_stdin:
            self.stdin.close()
            sys.stdin = self.stdin = self.backup_stdin
        return 0


class CommandParams(object):

    def __init__(self, name, args=None, stdout_path=None, stdout_mode='w',
                 stderr_path=None, stdin_path=None):
        self.name = name
        self.args = args or []
        self.stdout_path = stdout_path
        self.stdout_mode = stdout_mode
        self.stderr_path = stderr_path
        self.stdin_path = stdin_path


class StatementSyntaxError(Exception):

    def __init__(self, message, index):
        self.message = message
        self.index = index

    def __str__(self):
        return "syntax error at {}: {}".format(self.index, self.message)


class StatementParser(object):

    def __init__(self):
        pass

    def reset(self):
        self.tokens = []
        self.token = None

    def process(self, index, c):
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
            if c in (' ', '\t'):
                self.token = WhitespaceToken(index)
            elif c in ('>', '<', '|', '&', ';'):
                self.token = OperatorToken(index, c)
            else:
                self.token = StringToken(index, c)

    def tokenize(self, line):
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
        prev = None
        condensed = []
        for token in tokens:
            if isinstance(token, StringToken):
                if isinstance(prev, StringToken):
                    prev.text += token.text
                    token = prev
                else:
                    condensed.append(token)
            elif not isinstance(token, WhitespaceToken):
                condensed.append(token)
            prev = token

        return condensed

    def build(self, tokens, ctx):
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
        else:
            raise StatementSyntaxError(
                message="unexpected token: {}".format(str(prev)),
                index=prev.index
            )

        if cmd:
            statement.cmds.append(cmd)

        return statement
