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

from pypsi.core import Plugin, Command, PypsiArgParser, CommandShortCircuit
from pypsi.cmdline import StringToken, OperatorToken, Expression
import argparse


class AliasCommand(Command):

    def __init__(self, name='alias', brief='manage command aliases',
                 topic='shell', **kwargs):
        super(AliasCommand, self).__init__(name=name, brief=brief, topic=topic,
                                           **kwargs)

        self.parser = PypsiArgParser(prog=name, description=brief)
        self.parser.add_argument('-l', '--list', action='store_true',
                                 help='list registered aliases')

        self.parser.add_argument('exp', metavar='EXP', help='alias expression',
                                 nargs=argparse.REMAINDER)

        self.parser.add_argument('-d', '--delete', help='delete alias',
                                 nargs=1, metavar='ALIAS')

    def run(self, shell, args):
        try:
            ns = self.parser.parse_args(args)
        except CommandShortCircuit as e:
            return e.code

        rc = None
        if ns.list:
            for name in shell.ctx.aliases:
                print(name, "=", shell.ctx.aliases[name])
            rc = 0
        elif ns.delete:
            for name in ns.delete:
                if name in shell.ctx.aliases:
                    del shell.ctx.aliases[name]
                    rc = 0
                else:
                    self.error(shell, "alias does not exist: ", name)
                    rc = 1
                    break
        else:
            (remainder, exp) = Expression.parse(args)
            if remainder or not exp or exp.operator != '=':
                self.error(shell, "invalid expression")
                rc = 1
            else:
                shell.ctx.aliases[exp.operand] = exp.value
                rc = 0
        return rc


class AliasPlugin(Plugin):

    def __init__(self, preprocess=10, **kwargs):
        super(AliasPlugin, self).__init__(preprocess=preprocess, **kwargs)
        self.cmd = AliasCommand()

    def setup(self, shell):
        shell.ctx.aliases = {'print': 'echo Hello to you'}
        shell.register(self.cmd)
        return 0

    def on_tokenize(self, shell, tokens, origin):
        if origin != 'input':
            return tokens

        ret = []
        cmd = None
        for token in tokens:
            next = token
            if cmd:
                if (isinstance(token, OperatorToken) and
                        token.is_chain_operator()):
                    cmd = None
            else:
                if isinstance(token, StringToken):
                    cmd = token.text
                    if cmd in shell.ctx.aliases:
                        next = shell.parser.tokenize(shell.ctx.aliases[cmd])

            if next:
                if isinstance(next, list):
                    ret += next
                else:
                    ret.append(next)

        return ret
