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

import os
import sys
from typing import List
from pypsi.core import Command, PypsiArgParser, CommandShortCircuit
from pypsi.utils import safe_open
from pypsi.completers import path_completer
from pypsi.shell import Shell
from pypsi.ansi import Color


class IncludeCommand(Command):
    '''
    Execute a script file. This entails reading each line of the given file and
    processing it as if it were typed into the shell.
    '''

    def __init__(self, name='include', topic='shell', **kwargs):
        brief = 'execute a script file'
        self.parser = PypsiArgParser(prog=name, description=brief)

        self.parser.add_argument('path', metavar='PATH', action='store', help='file to execute',
                                 completer=path_completer)

        super().__init__(name=name, topic=topic, brief=brief, usage=self.parser.format_help(),
                         **kwargs)

    def setup(self, shell: Shell) -> None:
        shell.ctx.include_stack = []

    def complete(self, shell: Shell, args: List[str], prefix: str) -> List[str]:
        return self.parser.complete(shell, args, prefix)

    def run(self, shell: Shell, args: List[str]) -> int:
        try:
            ns = self.parser.parse_args(args)
        except CommandShortCircuit as e:
            return e.code

        return self.include_file(shell, ns.path)

    def include_file(self, shell: Shell, path: str) -> int:
        fp = None

        stack: List[str] = shell.ctx.include_stack
        filename = os.path.normcase(os.path.abspath(path))
        if filename in stack:
            self.error(f'recursive file include detected on {filename}')
            print(Color.bright_red('include stack:'), file=sys.stderr)

            for i, item in enumerate(stack, start=1):
                print(Color.bright_red(' ' * i, item), file=sys.stderr)

            return -1

        stack.append(filename)

        try:
            fp = safe_open(filename, 'r')
        except OSError as e:
            self.error(shell, f"failed to include file: {e.strerror}")
            return -1

        try:
            # Execute the lines in the file
            shell.include(fp)
            rc = shell.errno
        except Exception as e:  # pylint: disable=broad-except
            self.error(f"executing file {filename}: {e}")
            rc = -1

        stack.pop()
        fp.close()

        return rc
