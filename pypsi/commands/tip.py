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
from pypsi.stream import AnsiCodes
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

    def run(self, shell, args, ctx):
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

        i = self.rand.randrange(len(self.tips)) #int(self.rand.random() * len(self.tips)
        
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
            AnsiCodes.green,'>' * shell.width, "\n",
            AnsiCodes.reset,cnt, '\n',
            AnsiCodes.green,"<" * shell.width, "\n",
            AnsiCodes.reset,
            sep=''
        )
