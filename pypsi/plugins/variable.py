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

import argparse
from pypsi.core import Plugin, Command, PypsiArgParser, CommandShortCircuit
from pypsi.namespace import ScopedNamespace
from pypsi.cmdline import (Token, StringToken, TokenContinue, TokenEnd,
                           Expression)
from pypsi.format import Table, Column, obj_str
import os
import sys
from datetime import datetime


class ManagedVariable(object):
    '''
    Represents a variable that is managed by the shell. Managed variables have
    get and set hooks that allow for input validation or read-only enforcement.
    Each variable needs a ``getter``, which is called to retrieve the value,
    and possibly a ``setter``, which is called to set the value. If the setter
    is :const:`None`, the variable is read-only. The setter must accept two
    arguments when it is called: the active :class:`~pypsi.shell.Shell`
    instance, and the :class:`str` value.
    '''

    def __init__(self, getter, setter=None):
        '''
        :param callable getter: the callable to call when retrieving the
            variable's value (must return a value)
        :param callable setter: the callable to call when setting the
            variable's value
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

    Usage = """var name
   or: var EXPRESSION
   or: var -l
   or: var -d name"""

    def __init__(self, name='var', brief='manage local variables',
                 topic='shell', **kwargs):
        self.parser = PypsiArgParser(
            prog=name,
            description=brief,
            usage=VariableCommand.Usage
        )

        self.parser.add_argument(
            '-l', '--list', help='list variables', action='store_true'
        )
        self.parser.add_argument(
            '-d', '--delete', help='delete variable', metavar='VARIABLE'
        )
        self.parser.add_argument(
            'exp', metavar='EXPRESSION',
            help='expression defining variable, in the form of NAME = [VALUE]',
            nargs=argparse.REMAINDER
        )
        super(VariableCommand, self).__init__(
            name=name, usage=self.parser.format_help(), topic=topic,
            brief=brief, **kwargs
        )

    def run(self, shell, args):
        try:
            ns = self.parser.parse_args(args)
        except CommandShortCircuit as e:
            return e.code

        rc = 0
        if ns.list:
            tbl = Table(
                columns=(Column("Variable"), Column("Value", Column.Grow)),
                width=shell.width,
                spacing=4,
            )
            for name in shell.ctx.vars:
                if name == '_':
                    continue
                s = shell.ctx.vars[name]
                if callable(s):
                    s = s()
                elif isinstance(s, ManagedVariable):
                    s = s.get(shell)
                tbl.append(name, obj_str(s))
            tbl.write(sys.stdout)
        elif ns.delete:
            if ns.delete in shell.ctx.vars:
                s = shell.ctx.vars[ns.delete]
                if isinstance(s, ManagedVariable):
                    self.error(shell,
                               "variable is managed and cannot be deleted")
                    rc = -1
                else:
                    del shell.ctx.vars[ns.delete]
            else:
                self.error(shell, "unknown variable: ", ns.delete)
        elif ns.exp and '=' in ''.join(args):
            (remainder, exp) = Expression.parse(args)
            if remainder or not exp:
                self.error(shell, "invalid expression")
                return 1
            if isinstance(shell.ctx.vars[exp.operand], ManagedVariable):
                try:
                    shell.ctx.vars[exp.operand].set(shell, exp.value)
                except ValueError as e:
                    self.error(shell, "could not set variable: ", str(e))
            else:
                shell.ctx.vars[exp.operand] = exp.value
        elif ns.exp:
            if len(args) == 1:
                if args[0] in shell.ctx.vars:
                    s = shell.ctx.vars[args[0]]
                    if callable(s):
                        s = s()
                    elif isinstance(s, ManagedVariable):
                        s = s.getter(shell)
                    print(obj_str(s))
                else:
                    self.error(shell, "unknown variable: ", args[0])
                    return 1
            else:
                self.error(shell, "invalid expression")
                return 1
        else:
            self.usage_error(shell, "missing required EXPRESSION")
            rc = 1

        return rc


class VariableToken(Token):

    VarChars = ('abcdefghijklmnopqrstuvwxyz'
                'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
                '0123456789_')

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


def get_subtokens(token, prefix, features):
    escape = False
    index = token.index
    subt = None
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
                    subt = StringToken(index, c, token.quote,
                                       features=features)
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
                subt = StringToken(index, c, token.quote, features=features)
            else:
                subt.text += c
        index += 1

    if subt:
        yield subt
    elif var:
        yield var


def safe_date_format(format, dt):
    try:
        return dt.strftime(format)
    except:
        return "<invalid date time format>"


def var_date_getter(shell):
    return safe_date_format(shell.ctx.vars.datefmt or "%x", datetime.now())


def var_time_getter(shell):
    return safe_date_format(shell.ctx.vars.timefmt or "%X", datetime.now())


def var_datetime_getter(shell):
    return safe_date_format(shell.ctx.vars.datetimefmt or "%c", datetime.now())


def var_errno_getter(shell):
    return str(shell.errno)


def var_prompt_getter(shell):
    return shell.get_current_prompt()


class VariablePlugin(Plugin):
    '''
    Provides variable management and substitution in user input.
    '''

    def __init__(self, var_cmd='var', prefix='$', locals=None, env=True,
                 topic='shell', case_sensitive=True, preprocess=10,
                 postprocess=90, **kwargs):
        '''
        :param str var_cmd: the name of the variable command
        :param str prefix: the prefix that all variables need to start with
        :param dict locals: the base variables to register initially
        :param bool case_sensitive: whether variable names are case sensitive
        '''
        super(VariablePlugin, self).__init__(preprocess=preprocess,
                                             postprocess=postprocess, **kwargs)
        self.var_cmd = VariableCommand(name=var_cmd, topic=topic)
        self.prefix = prefix

        self.base = os.environ if env else {}
        self.case_sensitive = case_sensitive
        if locals:
            self.base.update(locals)

    def setup(self, shell):
        '''
        Register the :class:`VariableCommand` and add the ``vars`` attribute
        (:class:`pypsi.namespace.ScopedNamespace`) to the shell's context.
        '''
        shell.register(self.var_cmd)
        if 'vars' not in shell.ctx:
            shell.ctx.vars = ScopedNamespace('globals', self.case_sensitive)
            for k in self.base:
                shell.ctx.vars[k] = self.base[k]

            shell.ctx.vars.date = ManagedVariable(var_date_getter)
            shell.ctx.vars.time = ManagedVariable(var_time_getter)
            shell.ctx.vars.datetime = ManagedVariable(var_datetime_getter)
            shell.ctx.vars.prompt = ManagedVariable(var_prompt_getter,
                                                    self.set_prompt)
            shell.ctx.vars.errno = ManagedVariable(var_errno_getter)
        return 0

    def set_prompt(self, shell, value):
        shell.prompt = value

    def expand(self, shell, vart):
        name = vart.var
        if name in shell.ctx.vars:
            s = shell.ctx.vars[name]
            if callable(s):
                return s()
            elif isinstance(s, ManagedVariable):
                return s.getter(shell)
            return s
        return ''

    def on_tokenize(self, shell, tokens, origin):
        ret = []
        for token in tokens:
            if (not isinstance(token, StringToken) or
                    self.prefix not in token.text):
                ret.append(token)
                continue

            for subt in get_subtokens(token, self.prefix, shell.features):
                if isinstance(subt, StringToken):
                    ret.append(subt)
                    continue

                expanded = self.expand(shell, subt)
                '''
                if token.quote:
                    ret.append(StringToken(subt.index, expanded, token.quote))
                else:
                    ws = False
                    for part in shell.parser.tokenize(expanded):
                        ret.append(part)
                '''
                ret.append(StringToken(subt.index, expanded, '"'))

        return ret
