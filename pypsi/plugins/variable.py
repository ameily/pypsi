
from pypsi.base import Plugin, Preprocessor, Command
from pypsi.namespace import Namespace
from pypsi.cmdline import Token, StringToken, WhitespaceToken, TokenContinue, TokenEnd

try:
    from cStringIO import StringIO
except:
    from StrigIO import StringIO




class VariableCommand(Command):

    Usage = """usage: var name = value
Set a local variable."""

    def __init__(self, name='var', usage=Usage, **kwargs):
        super(VariableCommand, self).__init__(name=name, usage=usage, **kwargs)

    def run(self, shell, args, ctx):
        return 0


class VariableToken(Token):

    VarChars = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_'

    def __init__(self, prefix, index, var=''):
        super(VariableToken, self).__init__(index)
        self.prefix = prefix
        self.var = var

    def add_char(self, c):
        if c in self.VarChars:
            self.var += c
            return TokenContinue
        return TokenEnd


def get_subtokens(token, prefix):
    escape = False
    index = token.index
    subt = ''
    var = None
    for c in token.text:
        if escape:
            escape = False
            if c != prefix:
                subt.text += '\\'
            subt.text += c
        elif var:
            rc = var.add_char(c)
            if rc == TokenEnd:
                yield var
                if c == prefix:
                    var = VariableToken(index, c)
                else:
                    if c == '\\':
                        escape = True
                        c = ''
                    subt = StringToken(index, c, token.quote)
        elif c == prefix:
            if subt:
                yield subt
                subt = None
            var = VariableToken(c, index)
        else:
            if c == '\\':
                escape = True
                c = ''

            if not subt:
                subt = StringToken(index, c, token.quote)
            else:
                subt.text += c
        index += 1

    if subt:
        yield subt
    elif var:
        yield var


class VariablePlugin(Plugin, Preprocessor):

    def __init__(self, var_cmd='var', prefix='$', locals={}, case_sensitive=True, **kwargs):
        super(VariablePlugin, self).__init__(**kwargs)
        self.var_cmd = VariableCommand(name=var_cmd)
        self.prefix = prefix
        self.namespace = Namespace('locals', case_sensitive, **locals)

    def setup(self, shell):
        shell.register(self.var_cmd)
        shell.ctx.vars = self.namespace

    def expand(self, vart):
        name = vart.var
        if name in self.namespace:
            return self.namespace[name]
        return ''

    def on_tokenize(self, shell, tokens):
        ret = []
        for token in tokens:
            if not isinstance(token, StringToken) or self.prefix not in token.text:
                ret.append(token)
                continue

            for subt in get_subtokens(token, self.prefix):
                if isinstance(subt, StringToken):
                    ret.append(subt)
                    continue

                expanded = self.expand(subt)
                if token.quote:
                    ret.append(StringToken(subt.index, expanded, token.quote))
                else:
                    ws = False
                    for part in expanded.split():
                        if ws:
                            ret.append(WhitespaceToken(subt.index))
                        else:
                            ws = True
                        ret.append(StringToken(subt.index, part))

        return ret

