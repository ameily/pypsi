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

from pypsi.base import Plugin, Command
from pypsi.namespace import ScopedNamespace
from pypsi.cmdline import Token, StringToken, WhitespaceToken, TokenContinue, TokenEnd, Expression
import os
from datetime import datetime

from io import StringIO


class ManagedVariable(object):
    '''
    Represents a variable that is managed by the shell. Managed variables have 
    get and set hooks that allow for input validation or read-only enforcement.
    Each variable needs a ``getter``, which is called to retrieve the value, and
    possibly a ``setter``, which is called to set the value. If the setter is
    :const:`None`, the variable is read-only. The setter must accept two
    arguments when it is called: the active :class:`~pypsi.shell.Shell`
    instance, and the :class:`str` value.
    '''

    def __init__(self, getter, setter=None):
        '''
        :param callable getter: the callable to call when retrieving the
            variable's value (must return a value)
        :param callable setter: the callable to call when setting the variable's
            value
        '''
        self.getter = getter
        self.setter = setter

    def set(self, shell, value):
        if self.setter:
            self.setter(shell, value)
        else:
            raise ValueError("read-only variable")

    def get(self, shell):
        return self.getter(shell)


class VariableCommand(Command):
    '''
    Manage variables.
    '''

    Usage = """usage: var name = value
   or: var -l
   or: var -d name
Manage local variables."""

    def __init__(self, name='var', usage=Usage, **kwargs):
        super(VariableCommand, self).__init__(name=name, usage=usage, **kwargs)

    def run(self, shell, args, ctx):
        if not args:
            self.usage_error(shell, "missing required argument")
            return 1

        count = len(args)

        if args[0] == '-h':
            shell.warn(self.usage, '\n')
            return 0
        elif args[0] == '-l':
            if count != 1:
                self.error(shell, "invalid arguments\n")
                shell.warn(self.usage)
                return 1

            vars = []
            col1 = 0
            for name in shell.ctx.vars:
                s = shell.ctx.vars[name]
                col1 = max(col1, len(name))
                if callable(s):
                    s = s()
                elif isinstance(s, ManagedVariable):
                    s = s.getter(shell)
                vars.append((name, s))
            vars = sorted(vars, key=lambda x: x[0])
            for v in vars:
                shell.info(
                    v[0], ' ' * (col1 - len(v[0])), '    ', v[1], '\n'
                )
        elif args[0] == '-d':
            if count != 2:
                self.error(shell, "invalid arguments\n")
                shell.warn(self.usage)
                return 1

            name = args[1]
            if name in shell.ctx.vars:
                del shell.ctx.vars[name]
            return 0
        else:
            (remaining, exp) = Expression.parse(args)
            if remaining:
                self.usage_error(shell, "cannot set multiple variables")
                return 1

            if exp.operand is None:
                self.usage_error(shell, "missing variable name")
                return 1

            if exp.operator is None:
                self.usage_error(shell, "missing operator")
                return 1

            if exp.operator != '=':
                self.usage_error(shell, "invalid operator ", exp.operator)
                return 1

            if exp.value is None:
                #self.usage_error(shell, "missing value")
                #return 1
                exp.value = ''

            try:
                name = exp.operand
                value = exp.value
                if name in shell.ctx.vars and isinstance(shell.ctx.vars[name], ManagedVariable):
                    shell.ctx.vars[name].set(shell, value)
                else:
                    shell.ctx.vars[name] = value
            except ValueError as e:
                self.error(shell, "error setting variable ", name, ": ", e.message, '\n')

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

    def __str__(self):
        return "VariableToken( {} )".format(self.var)


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
                var = None
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


class VariablePlugin(Plugin):
    '''
    Provides variable management and substitution in user input.
    '''

    def __init__(self, var_cmd='var', prefix='$', locals=None,
                 case_sensitive=True, preprocess=10, postprocess=90, **kwargs):
        '''
        :param str var_cmd: the name of the variable command
        :param str prefix: the prefix that all variables need to start with
        :param dict locals: the base variables to register initially
        :param bool case_sensitive: whether variable names are case sensitive
        '''
        super(VariablePlugin, self).__init__(preprocess=preprocess, postprocess=postprocess, **kwargs)
        self.var_cmd = VariableCommand(name=var_cmd)
        self.prefix = prefix
        self.namespace = ScopedNamespace('globals', case_sensitive, os.environ)
        if locals:
            for (k, v) in locals:
                self.namespace[k] = v

    def setup(self, shell):
        '''
        Register the :class:`VariableCommand` and add the ``vars`` attribute
        (:class:`pypsi.namespace.ScopedNamespace`) to the shell's context.
        '''
        shell.register(self.var_cmd)
        if 'vars' not in shell.ctx:
            shell.ctx.vars = self.namespace
            shell.ctx.vars.date = ManagedVariable(lambda shell: datetime.now().strftime(shell.ctx.vars.datefmt or "%x"))
            shell.ctx.vars.time = ManagedVariable(lambda shell: datetime.now().strftime(shell.ctx.vars.timefmt or "%X"))
            shell.ctx.vars.datetime = ManagedVariable(lambda shell: datetime.now().strftime(shell.ctx.vars.datetimefmt or "%c"))
            shell.ctx.vars.prompt = ManagedVariable(lambda shell: shell.prompt)
            shell.ctx.vars.errno = ManagedVariable(lambda shell: str(shell.errno))
        return 0

    def expand(self, shell, vart):
        name = vart.var
        if name in self.namespace:
            s = self.namespace[name]
            if callable(s):
                return s()
            elif isinstance(s, ManagedVariable):
                return s.getter(shell)
            return s
        return ''

    def on_tokenize(self, shell, tokens, origin):
        ret = []
        for token in tokens:
            if not isinstance(token, StringToken) or self.prefix not in token.text:
                ret.append(token)
                continue

            for subt in get_subtokens(token, self.prefix):
                if isinstance(subt, StringToken):
                    ret.append(subt)
                    continue

                expanded = self.expand(shell, subt)
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

    def on_statement_finished(self, shell):
        pass
