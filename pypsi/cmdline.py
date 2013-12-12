
TokenContinue = 0   # keep going
TokenEnd = 1        # c ends token, process c again
TokenTerm = 2       # c terms token
TokenTransform = 3  # transform token


class ParserContext(object):

    def __init__(self, case_sensitive, vars):
        self.case_sensitive = case_sensitive
        self.vars = vars

    def expand_var(self, prefix, name):
        if not self.vars:
            return ''

        if prefix not in self.vars:
            return ''

        if not self.case_sensitive:
            name = name.lower()

        if name in self.vars[prefix]:
            return self.vars[prefix][name]

        return ''


class Token(object):

    def __init__(self, index, ctx=None):
        self.index = index
        self.ctx = ctx
        self.transform = None


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

    def __init__(self, index, ctx, c, literal=False):
        super(StringToken, self).__init__(index, ctx)
        self.quote = None
        self.escape = False
        self.text = ''
        self.var = None

        if literal:
            self.text = c
        else:
            if c in ('"', "'"):
                self.quote = c
            elif c == '\\':
                self.escape = True
            else:
                self.text += c

    def expand_var(self):
        self.text += self.var.expand(True)
        self.var = None

    def add_char(self, c):
        if self.var:
            if self.var.add_char(c) == TokenEnd:
                self.expand_var()
            else:
                return

        ret = TokenContinue
        if self.escape:
            self.escape = False
            if self.quote:
                if c == self.quote:
                    self.text += c
                elif c == '\\':
                    self.escape = True
                    self.text += '\\'
                else:
                    self.text += '\\'
                    self.text += c
            else:
                self.text += c
        elif self.quote:
            if c == self.quote:
                self.quote = False
            elif c in ('$', '%'):
                self.var = VariableToken(self.index + len(self.text), self.ctx, c)
            elif c == '\\':
                self.escape = True
            else:
                self.text += c
        else:
            if c == '\\':
                self.esacpe = True
            elif c in (' ', '\t', ';', '|', '&', '>', '<', '$', '%'):
                ret = TokenEnd
            else:
                self.text += c
        return ret

    def __str__(self):
        return "String({quote}{text}{quote})".format(
            quote=self.quote or '',
            text=self.text
        )


class VariableToken(Token):

    def __init__(self, index, ctx, prefix):
        super(VariableToken, self).__init__(index, ctx)
        self.prefix = prefix
        self.var = ''

    def add_char(self, c):
        if c in ('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_'):
            self.var += c
            return TokenContinue
        return TokenEnd

    def expand(self, literal):
        expanded = self.ctx.expand_var(self.prefix, self.var)
        if literal:
            return expanded

        words = expanded.split()
        count = len(words)
        tokens = []
        for i in range(count):
            if i > 0:
                tokens.append(WhitespaceToken(self.index))
            tokens.append(StringToken(self.index, None, words[i], True))

        return tokens

    def __str__(self):
        return "VariableToken({}{})".format(
            self.prefix,
            self.var
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
        return "OperatorToken({})".format(self.operator)




class CommandContext(object):

    def __init__(self, name, args=[], stdout=None, stdin=None, pipe=None):
        self.name = name
        self.args = args
        self.stdout = stdout
        self.stdin = stdin
        self.pipe = pipe

    def __str__(self):
        s = '"' + self.name.replace('"', '\\"') + '"'
        s += ' '
        s += str(self.args)
        s += ' '
        if self.stdout:
            s += self.stdout[0] + " " + self.stdout[1] + ' '

        if self.stdin:
            s += '< ' + self.stdin + ' '

        #if self.next:
        #    s += "<" + self.next + ">"
        return s



class StatementSyntaxError(Exception):

    def __init__(self, message, index):
        self.message = message
        self.index = index

    def __str__(self):
        return "syntax error at {}: {}".format(self.index, self.message)


class StatementParser(object):

    def __init__(self, case_sensitive):
        self.case_sensitive = case_sensitive

    def reset(self):
        self.tokens = []
        self.token = None
        self.ctx = None

    def process(self, index, c):
        if self.token:
            action = self.token.add_char(c)
            if action == TokenTransform:
                self.token = self.token.transform
            elif action == TokenEnd:
                if isinstance(self.token, VariableToken):
                    self.tokens.extend(self.token.expand(False))
                else:
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
            elif c in ('$', '%'):
                self.token = VariableToken(index, self.ctx, c)
            elif c in ('>', '<', '|', '&', ';'):
                self.token = OperatorToken(index, c)
            else:
                self.token = StringToken(index, self.ctx, c)

    def tokenize(self, line, vars=None):
        self.reset()
        self.ctx = ParserContext(self.case_sensitive, vars)
        index = 0
        for c in line:
            self.process(index, c)
            index += 1

        if self.token:
            self.tokens.append(self.token)

        return self.tokens

    def condense(self, tokens):
        prev = None
        condensed = []
        for token in tokens:
            if isinstance(token, StringToken):
                if isinstance(prev, StringToken):
                    prev.text += token.text
                else:
                    condensed.append(token)
            elif not isinstance(token, WhitespaceToken):
                condensed.append(token)
            prev = token

        return condensed

    def build(self, tokens):
        cmds = []
        cmd = None
        prev = None
        tokens = self.condense(tokens)

        for token in tokens:
            if cmd:
                if isinstance(prev, OperatorToken) and prev.operator in ('>', '<', '>>'):
                    if isinstance(token, StringToken):
                        if prev.operator in ('>', '>>'):
                            cmd.stdout[1] = token.text
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
                    done = True
                    if token.operator == '||':
                        cmd.next = 'or'
                    elif token.operator == '&&':
                        cmd.next = 'and'
                    elif token.operator == ';':
                        cmd.next = 'chain'
                    elif token.operator == '|':
                        if cmd.stdout:
                            raise StatementSyntaxError(
                                message="unexpected token: {}".format(str(token)),
                                index=token.index
                            )

                        cmd.next = 'pipe'
                    elif token.operator in ('>', '>>'):
                        if cmd.stdout:
                            raise StatementSyntaxError(
                                message="unexpected token: {}".format(str(token)),
                                index=token.index
                            )

                        cmd.stdout = ['trunc' if token.operator == '>' else 'append', '']
                        done = False
                    elif token.operator == '<':
                        if cmd.stdin:
                            raise StatementSyntaxError(
                                message="unexpected token: {}".format(str(token)),
                                index=token.index
                            )

                        if cmds and cmds[-1].next == 'pipe':
                            raise StatementSyntaxError(
                                message="unexpected token: {}".format(str(token)),
                                index=token.index
                            )

                        cmd.stdin = ''
                        done = False
                    else:
                        raise StatementSyntaxError(
                            message="unknown operator: {}".format(token.operator),
                            index=token.index
                        )

                    if done:
                        cmds.append(cmd)
                        cmd = None
            else:
                if isinstance(token, StringToken):
                    cmd = CommandContext(token.text)
                elif not isinstance(token, WhitespaceToken):
                    raise StatementSyntaxError(
                        message="unexpected token: {}".format(str(token)),
                        index=token.index
                    )
            prev = token

        if not isinstance(prev, StringToken):
            raise StatementSyntaxError(
                message="unexpected token: {}".format(str(prev)),
                index=prev.index
            )

        if cmd:
            cmds.append(cmd)

        return cmds


if __name__ == "__main__":
    parser = StatementParser(False)
    vars = { '$': { 'name': 'Adam Meily', 'x': '2 + 3'}}
    t = r'   some-cmd $name "long String $X"adam <file.txt | other-cmd || last > output'
    print t
    tokens = parser.tokenize(
        t, vars
    )

    cmdline = parser.build(tokens)

    print
    print "=== Commands ==="
    for cmd in cmdline:
        print str(cmd)
