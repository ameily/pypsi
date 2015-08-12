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
from pypsi.ansi import AnsiCodes
from pypsi.utils import safe_open
import random
import sys


class TipCommand(Command):

    def __init__(self, name='tip', brief='print shell tips', topic='shell',
                 tips=None, motd=None, vars=None, **kwargs):
        self.tips = tips or []
        self.motd = motd or ''
        self.vars = vars or {}
        self.rand = random.Random()
        self.rand.seed()

        self.parser = PypsiArgParser(
            prog=name,
            description=brief
        )

        self.parser.add_argument(
            '-m', '--motd', action='store_true',
            help="print the message of the day"
        )

        super(TipCommand, self).__init__(
            name=name, brief=brief, topic=topic,
            usage=self.parser.format_help(), **kwargs
        )

    def load_tips(self, path):
        fp = safe_open(path, 'r')
        tip = []
        for line in fp.readlines():
            line = line.rstrip()
            if line:
                tip.append(line)
            elif tip:
                self.tips.append(' '.join(tip))
                tip = []
        if tip:
            self.tips.append(' '.join(tip))
        fp.close()

    def load_motd(self, path):
        fp = safe_open(path, 'r')
        self.motd = fp.read().rstrip()
        fp.close()

    def run(self, shell, args):
        try:
            ns = self.parser.parse_args(args)
        except CommandShortCircuit as e:
            return e.code

        rc = None
        if ns.motd:
            rc = self.print_motd(shell)
        else:
            rc = self.print_random_tip(shell)

        return rc

    def print_random_tip(self, shell, header=True):
        if not self.tips:
            self.error(shell, "no tips available")
            return -1

        i = self.rand.randrange(len(self.tips))

        if header:
            title = "Tip #{}\n".format(i+1)
            title += '-' * len(title)
            print(AnsiCodes.green, title, AnsiCodes.reset, sep='')

        try:
            cnt = sys.stdout.ansi_format(self.tips[i], **self.vars)
        except:
            cnt = self.tips[i]

        print(cnt)

    def print_motd(self, shell):
        if not self.motd:
            self.error(shell, "no motd available")
            return -1

        try:
            cnt = sys.stdout.ansi_format(self.motd, **self.vars)
        except:
            cnt = self.motd

        print(
            AnsiCodes.green,
            "Message of the Day".center(shell.width), '\n',
            AnsiCodes.green, '>' * shell.width, "\n",
            AnsiCodes.reset, cnt, '\n',
            AnsiCodes.green, "<" * shell.width, "\n",
            AnsiCodes.reset,
            sep=''
        )
