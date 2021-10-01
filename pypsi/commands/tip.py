#
# Copyright (c) 2021, Adam Meily <meily.adam@gmail.com>
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

import random
import sys
from typing import List
from pypsi.shell import Shell
from pypsi.core import Command, PypsiArgParser, CommandShortCircuit
from pypsi.ansi import Color, ansi_title
from pypsi.utils import safe_open


class TipCommand(Command):

    def __init__(self, name='tip', topic='shell', tips: List[str] = None, motd: str = None,
                 **kwargs):
        self.tips = tips or []
        self.motd = motd or ''
        self.rand = random.Random()
        self.rand.seed()

        brief = 'print shell tips'

        self.parser = PypsiArgParser(prog=name, description=brief)

        self.parser.add_argument('-m', '--motd', action='store_true',
                                 help="print the message of the day")

        super().__init__(name=name, brief=brief, topic=topic, usage=self.parser.format_help(),
                         **kwargs)

    def load_tips(self, path: str) -> None:
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

    def load_motd(self, path: str) -> None:
        fp = safe_open(path, 'r')
        self.motd = fp.read().rstrip()
        fp.close()

    def run(self, shell: Shell, args: List[str]) -> int:
        try:
            ns = self.parser.parse_args(args)
        except CommandShortCircuit as e:
            return e.code

        rc = None
        if ns.motd:
            rc = self.print_motd()
        else:
            rc = self.print_random_tip()

        return rc

    def print_random_tip(self) -> int:
        if not self.tips:
            self.error("no tips available")
            return -1

        i = self.rand.randrange(len(self.tips))

        print(Color.bright_green(ansi_title(f"Tip #{i + 1}")))
        print(self.tips[i])
        return 0

    def print_motd(self) -> int:
        if not self.motd:
            self.error("no message of the day available")
            return -1

        width = sys.stdout.width
        print(Color.bright_green("Message of the Day".center(width)))
        print(Color.bright_green('>' * width))
        print(self.motd)
        print(Color.bright_green("<" * width))
        return 0
