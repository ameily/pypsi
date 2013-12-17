
from pypsi.base import Plugin, Preprocessor, Command
from pypsi.namespace import Namespace
from pypsi.cmdline import StringToken, WhitespaceToken
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


class VariableExpander(object):

    def __init__(self, prefix, namespace):
        self.prefix = prefix
        self.namespace = namespace
        self.reset()

    def reset(self):
        self.escape = False
        self.var = None
        self.tokens = []
        self.text = StringIO()
        self.token = None

    def expand(self, name):
        value = self.namespace[name] if name in self.namespace else ''
        if not self.token.quote:
            first = True
            for s in value.split():
                if first:
                    first = False
                else:
                    self.tokens.append(WhitespaceToken(self.token.index))

                self.tokens.append(
                    StringToken(
                        c=s,
                        ctx=None,
                        index=self.token.index,
                        quote=self.token.quote
                    )
                )
        else:
            self.tokens.append(
                StringToken(
                    c=value,
                    ctx=None,
                    index=self.token.index,
                    quote=self.token.quote
                )
            )

    def process(self, c, index):
        if self.escape:
            self.escape = False
            if c != self.prefix:
                self.text.write('\\')
            self.text.write(c)
        elif self.var is not None:
            if c in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_?#':
                self.var += c
            else:
                self.expand(self.var)
                self.var = None
                self.process(c, index)
        elif c == self.prefix:
            self.var = ''
            val = self.text.getvalue()
            if val:
                self.tokens.append(
                    StringToken(
                        c=val,
                        ctx=None,
                        index=self.token.index,
                        quote=self.token.quote
                    )
                )
                self.text = StringIO()
        else:
            self.text.write(c)

    def get_tokens(self, token):
        self.reset()
        self.token = token
        index = 0
        for c in token.text:
            self.process(c, index)
            index += 1

        if self.var:
            self.expand(self.var)
        elif self.var == '':
            self.tokens.append(
                StringToken(
                    c=self.prefix,
                    quote=self.token.prefix,
                    ctx=None,
                    index=self.token.index+index
                )
            )

        value = self.text.getvalue()
        if value:
            print "value:",value
            self.tokens.append(
                StringToken(
                    c=value,
                    index=self.token.index+index,
                    quote=self.token.quote,
                    ctx=None
                )
            )
            print "tokens:", ', '.join([t.text for t in self.tokens])

        self.token = None
        return self.tokens


class VariablePlugin(Plugin, Preprocessor):

    def __init__(self, var_cmd='var', prefix='$', locals={}, **kwargs):
        super(VariablePlugin, self).__init__(**kwargs)
        self.var_cmd = VariableCommand(name=var_cmd)
        self.prefix = prefix
        self.namespace = Namespace('locals', **locals)
        self.parser = VariableExpander(self.prefix, self.namespace)

    def setup(self, shell):
        shell.register(self.var_cmd)



    def on_tokenize(self, shell, tokens):
        ret = []
        for token in tokens:
            if not isinstance(token, StringToken) or self.prefix not in token.text:
                ret.append(token)
                continue

            ret.extend(self.parser.get_tokens(token))

        return ret

