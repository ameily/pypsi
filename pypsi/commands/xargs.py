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

from pypsi.base import Command, PypsiArgParser, CommandShortCircuit
import sys
import argparse

XArgsUsage = """{name} [-h] [-I REPSTR] COMMAND"""


class XArgsCommand(Command):
    '''
    Execute a command for each line of input from :data:`sys.stdin`.
    '''

    def __init__(self, name='xargs', topic='shell', brief='build and execute command lines from stdin', **kwargs):
        self.parser = PypsiArgParser(
            prog=name,
            description=brief,
            usage=XArgsUsage.format(name=name)
        )

        self.parser.add_argument(
            '-I', default='{}', action='store',
            metavar='REPSTR', help='string token to replace',
            dest='token'
        )

        self.parser.add_argument(
            'command', nargs=argparse.REMAINDER, help="command to execute",
            metavar='COMMAND'
        )

        super(XArgsCommand, self).__init__(
            name=name, topic=topic, usage=self.parser.format_help(),
            brief=brief, **kwargs
        )

    def run(self, shell, args, ctx):
        try:
            ns = self.parser.parse_args(args)
        except CommandShortCircuit as e:
            return e.code

        if not ns.command:
            self.error(shell, "missing command")
            return 1

        base = ' '.join([
            '"{}"'.format(c.replace('"', '\\"')) for c in ns.command
        ])

        child = ctx.fork()
        for line in sys.stdin:
            cmd = base.replace(ns.token, line.strip())
            shell.execute(cmd, child)

        return 0
