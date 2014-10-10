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

from pypsi.base import Plugin, Command, PypsiArgParser, CommandShortCircuit
from pypsi.cmdline import StringToken, OperatorToken, Expression
import argparse


class AliasCommand(Command):

    def __init__(self, name='alias', brief='manage command aliases',
                 topic='shell', **kwargs):
        super(AliasCommand, self).__init__(name=name, brief=brief, topic=topic, **kwargs)

        self.parser = PypsiArgParser(prog=name, description=brief)
        self.parser.add_argument('-l', '--list', help='list registered aliases',
                                 action='store_true')

        self.parser.add_argument('exp', metavar='EXP', help='alias expression',
                                 nargs=argparse.REMAINDER)

        self.parser.add_argument('-d', '--delete', help='delete alias', nargs=1,
                                 metavar='ALIAS')

    def run(self, shell, args, ctx):
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
        shell.ctx.aliases = { 'print': 'echo Hello to you' }
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
                if isinstance(token, OperatorToken) and token.is_chain_operator():
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
