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

import os
from typing import List
from pypsi.shell import Shell
from pypsi.completers import path_completer
from pypsi.core import Command, PypsiArgParser, CommandShortCircuit


class ChdirCommand(Command):
    '''
    Change the current working directory. This accepts one of the following:

    * <path> - a relative or absolute path
    * ~ - the current user's home directory
    * ~<user> - <user>'s home directory
    * - - the previous directory
    '''

    def __init__(self, name='cd', topic='shell', **kwargs):
        brief = 'change current working directory'

        self.parser = PypsiArgParser(prog=name, description=brief)
        self.parser.add_argument('path', help='path', metavar="PATH", completer=path_completer)
        super().__init__(name=name, brief=brief, topic=topic, usage=self.parser.format_help(),
                         **kwargs)

    def setup(self, shell: Shell):
        shell.ctx.chdir_last_dir = os.getcwd()

    def complete(self, shell: Shell, args: List[str], prefix: str) -> List[str]:
        return self.parser.complete(shell, args, prefix)

    def chdir(self, shell: Shell, path: str, print_cwd: bool = False) -> int:
        prev = os.getcwd()
        try:
            os.chdir(path)
            if print_cwd:
                print(os.getcwd())
        except OSError as e:
            self.error(f'{path}: {e.strerror}')
            return -1

        shell.ctx.chdir_last_dir = prev
        return 0

    def run(self, shell, args):
        try:
            ns = self.parser.parse_args(args)
        except CommandShortCircuit as e:
            return e.code

        if ns.path == '-':
            return self.chdir(shell, shell.ctx.chdir_last_dir, True)

        return self.chdir(shell, os.path.expanduser(ns.path))
