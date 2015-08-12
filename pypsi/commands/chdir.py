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
import os


class ChdirCommand(Command):
    '''
    Change the current working directory. This accepts one of the following:

    * <path> - a relative or absolute path
    * ~ - the current user's home directory
    * ~<user> - <user>'s home directory
    * - - the previous directory
    '''

    def __init__(self, name='cd', brief='change current working directory',
                 topic='shell', **kwargs):
        super(ChdirCommand, self).__init__(name=name, brief=brief, topic=topic,
                                           **kwargs)

        self.parser = PypsiArgParser(prog=name, description=brief)
        self.parser.add_argument('path', help='path', metavar="PATH")

    def setup(self, shell):
        shell.ctx.chdir_last_dir = os.getcwd()

    def chdir(self, shell, path, print_cwd=False):
        prev = os.getcwd()
        try:
            os.chdir(path)
            if print_cwd:
                print(os.getcwd())
        except OSError as e:
            self.error(shell, path, ": ", e.strerror)
            return -1
        except Exception as e:
            self.error(shell, path, ": ", str(e))
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

        if ns.path.startswith('~'):
            return self.chdir(shell, os.path.expanduser(ns.path))

        return self.chdir(shell, ns.path)
