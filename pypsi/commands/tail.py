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
from pypsi.shell import Shell
from pypsi.core import Command, PypsiArgParser, CommandShortCircuit
from pypsi.completers import path_completer
from pypsi.utils import safe_open


class TailCommand(Command):
    '''
    Displays the last N lines of a file to the screen.
    '''

    def __init__(self, name='tail', topic='shell', **kwargs):
        brief = 'display the last lines of a file'
        self.parser = PypsiArgParser(prog=name, description=brief)

        # Add a callback function that will be called when the
        # argument is tab-completed
        self.parser.add_argument('input_file', help='file to display', metavar="FILE",
                                 completer=path_completer)

        self.parser.add_argument('-n', '--lines', metavar="N", type=int, default=10,
                                 help="number of lines to display")

        super().__init__(name=name, usage=self.parser.format_help(), topic=topic, brief=brief,
                         **kwargs)

    def run(self, shell: Shell, args: List[str]):
        try:
            ns = self.parser.parse_args(args)
        except CommandShortCircuit as e:
            return e.code

        # print the last N lines
        try:
            last_lines = self.tail(ns.input_file, ns.lines)
        except OSError as err:
            self.error(f'failed to open file {ns.input_file}: {err.strerror}')
            return err.errno or -1

        for line in last_lines:
            print(line)

        print()

        return 0

    def complete(self, shell: Shell, args: List[str], prefix: str) -> List[str]:
        # The command_completer function takes in the parser, automatically
        # completes optional arguments (ex, '-v'/'--verbose') or sub-commands,
        # and complete any arguments' values by calling a callback function
        # with the same arguments as complete if the callback was defined
        # when the parser was created.
        return self.parser.complete(shell, args, prefix)

    def tail(self, filename: str, lines: int = 10, block_size: int = 1024) -> str:
        data = []
        blocks = -1
        num_lines = 0

        with safe_open(filename, 'r') as fp:
            # seek to the end and get the number of bytes in the file
            fp.seek(0, 2)
            num_bytes = fp.tell()
            bytes_left = num_bytes

            while num_lines < lines and bytes_left > 0:
                if bytes_left - block_size > 0:
                    # Seek back a block_size
                    fp.seek(num_bytes - (blocks * block_size))
                    # read data from file
                    data.insert(0, fp.read(block_size))
                else:
                    # jump back to the beginning
                    fp.seek(0, 0)
                    # read data
                    data.insert(0, fp.read(num_bytes))
                num_lines = data[0].count('\n')
                bytes_left -= block_size
                blocks -= 1

            return ''.join(data).splitlines()[-lines:]
