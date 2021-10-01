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

from typing import List
import sys
import argparse
from pypsi.shell import Shell
from pypsi.core import Command, PypsiArgParser, CommandShortCircuit


class XArgsCommand(Command):
    '''
    Execute a command for each line of input from :data:`sys.stdin`.
    '''

    def __init__(self, name='xargs', topic='shell', **kwargs):
        brief = 'build and execute command lines from stdin'
        self.parser = PypsiArgParser(prog=name, description=brief)

        self.parser.add_argument('-I', default='{}', action='store', metavar='REPSTR',
                                 help='string token to replace', dest='token')

        self.parser.add_argument('command', nargs=argparse.REMAINDER, help="command to execute",
                                 metavar='COMMAND')

        super().__init__(name=name, topic=topic, usage=self.parser.format_help(), brief=brief,
                         **kwargs)

    def run(self, shell: Shell, args: List[str]) -> int:
        try:
            ns = self.parser.parse_args(args)
        except CommandShortCircuit as e:
            return e.code

        if not ns.command:
            self.error(shell, "missing command")
            return 1

        # pylint: disable=consider-using-f-string
        base = ' '.join('"{}"'.format(c.replace('"', f'{shell.profile.escape_char}"'))
                        for c in ns.command)

        rc = 0
        for line in sys.stdin:
            cmd = base.replace(ns.token, line.strip())
            rc = shell.execute(cmd)

        return rc
