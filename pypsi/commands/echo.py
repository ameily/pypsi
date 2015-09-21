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

from pypsi.core import Command, PypsiArgParser, CommandShortCircuit
import argparse

EchoCmdUsage = "%(prog)s [-n] [-h] message"


class EchoCommand(Command):
    '''
    Prints text to the screen.
    '''

    def __init__(self, name='echo', topic='shell',
                 brief='print a line of text', **kwargs):
        self.parser = PypsiArgParser(
            prog=name,
            description=brief,
            usage=EchoCmdUsage
        )

        self.parser.add_argument(
            'message', help='message to print', nargs=argparse.REMAINDER,
            metavar="MESSAGE"
        )

        self.parser.add_argument(
            '-n', '--nolf', help="don't print newline character",
            action='store_true'
        )

        super(EchoCommand, self).__init__(
            name=name, usage=self.parser.format_help(), topic=topic,
            brief=brief, **kwargs
        )

    def run(self, shell, args):
        try:
            ns = self.parser.parse_args(args)
        except CommandShortCircuit as e:
            return e.code

        tail = '' if ns.nolf else '\n'

        print(' '.join(ns.message), sep='', end=tail)

        return 0
