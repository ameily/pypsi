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

EchoCmdUsage = "%(prog)s [-n] [-h] message"


class EchoCommand(Command):
    '''
    Prints text to the screen.
    '''

    def __init__(self, name='echo', topic='shell', brief='print a line of text', **kwargs):
        self.parser = PypsiArgParser(
            prog=name,
            description=brief,
            usage=EchoCmdUsage
        )

        subcmd = self.parser.add_argument_group(title='Stream')

        self.parser.add_argument(
            'message', help='message to print', nargs=argparse.REMAINDER,
            metavar="MESSAGE"
        )

        self.parser.add_argument(
            '-n', '--nolf', help="don't print newline character", action='store_true'
        )

        super(EchoCommand, self).__init__(
            name=name, usage=self.parser.format_help(), topic=topic,
            brief=brief, **kwargs
        )

    def run(self, shell, args, ctx):
        try:
            ns = self.parser.parse_args(args)
        except CommandShortCircuit as e:
            return e.code

        tail = '' if ns.nolf else '\n'

        print(' '.join(ns.message), sep='', end=tail)

        return 0
