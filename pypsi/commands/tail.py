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
from pypsi.completers import path_completer, command_completer
import time
import os

TailCmdUsage = "%(prog)s [-n N] [-f] [-h] FILE"


class TailCommand(Command):
    '''
    Displays the last N lines of a file to the screen.
    '''

    def __init__(self, name='tail', topic='shell',
                 brief='display the last lines of a file', **kwargs):
        self.parser = PypsiArgParser(
            prog=name,
            description=brief,
            usage=TailCmdUsage
        )

        # Add a callback function that will be called when the
        # argument is tab-completed
        self.parser.add_argument(
            'input_file', help='file to display',
            metavar="FILE", completer=self.complete_path
        )

        self.parser.add_argument(
            '-n', '--lines', metavar="N", type=int, default=10,
            help="number of lines to display"
        )

        self.parser.add_argument(
            '-f', '--follow', help="continue to output as file grows",
            action='store_true'
        )

        super(TailCommand, self).__init__(
            name=name, usage=self.parser.format_help(), topic=topic,
            brief=brief, **kwargs
        )

    def run(self, shell, args):
        try:
            ns = self.parser.parse_args(args)
        except CommandShortCircuit as e:
            return e.code

        # check for valid input file
        if not os.path.isfile(ns.input_file):
            self.error(shell, "invalid file path: ", ns.input_file, "\n")
            return -1

        # print the last N lines
        last_lines = self.tail(ns.input_file, ns.lines)
        for line in last_lines:
            print(line)
        print()

        # continue to follow the file and display new content
        if ns.follow:
            self.follow_file(ns.input_file)

        return 0

    def complete_path(self, shell, args, prefix):
        return path_completer(args[-1])

    def complete(self, shell, args, prefix):
        # The command_completer function takes in the parser, automatically
        # completes optional arguments (ex, '-v'/'--verbose') or sub-commands,
        # and complete any arguments' values by calling a callback function
        # with the same arguments as complete if the callback was defined
        # when the parser was created.
        return command_completer(self.parser, shell, args, prefix)

    def tail(self, fname, lines=10, block_size=1024):
        data = []
        blocks = -1
        num_lines = 0

        with open(fname) as fp:
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

    def follow_file(self, fname):
        with open(fname) as fp:
            # jump to the end of the file
            fp.seek(0, 2)
            try:
                while 1:
                    where = fp.tell()
                    line = fp.readline()
                    if not line:
                        time.sleep(1)
                        fp.seek(where)
                    else:
                        print(line, end='', flush=True)
            except (KeyboardInterrupt):
                print()
                return 0

        return 0
