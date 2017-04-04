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
from pypsi.utils import safe_open
from pypsi.completers import path_completer
import os


class IncludeFile(object):

    def __init__(self, path):
        self.name = os.path.basename(path)
        self.abspath = os.path.abspath(path)


class IncludeCommand(Command):
    '''
    Execute a script file. This entails reading each line of the given file and
    processing it as if it were typed into the shell.
    '''

    def __init__(self, name='include', topic='shell',
                 brief='execute a script file', **kwargs):
        self.parser = PypsiArgParser(
            prog=name,
            description=brief
        )

        self.parser.add_argument(
            'path', metavar='PATH', action='store', help='file to execute'
        )

        super(IncludeCommand, self).__init__(
            name=name, topic=topic, brief=brief,
            usage=self.parser.format_help(), **kwargs
        )
        self.stack = []

    def complete(self, shell, args, prefix):
        return path_completer(args[-1])

    def run(self, shell, args):
        try:
            ns = self.parser.parse_args(args)
        except CommandShortCircuit as e:
            return e.code

        return self.include_file(shell, ns.path)

    def include_file(self, shell, path):
        fp = None
        ifile = IncludeFile(path)

        if self.stack:
            for i in self.stack:
                if i.abspath == ifile.abspath:
                    self.error(shell, "recursive include for file ",
                               ifile.abspath, '\n')
                    return -1

        self.stack.append(ifile)

        try:
            fp = safe_open(path, 'r')
        except (OSError, IOError) as e:
            self.error(shell, "error opening file {}: {}".format(path, str(e)))
            return -1

        try:
            # Execute the lines in the file
            shell.include(fp)
        except Exception as e:
            self.error(shell, "error executing file ", path, ": ", str(e))

        self.stack.pop()
        fp.close()

        return 0
