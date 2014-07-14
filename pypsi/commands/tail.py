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
from pypsi.completers import path_completer
import time
import os

TailCmdUsage = "%(prog)s [-n N] [-f] [-h] FILE"


class TailCommand(Command):
    '''
    Displays the last N lines of a file to the screen.
    '''

    def __init__(self, name='tail', topic='shell', brief='display the last lines of a file', **kwargs):
        self.parser = PypsiArgParser(
            prog=name,
            description=brief,
            usage=TailCmdUsage
        )

        self.parser.add_argument(
            'input_file', help='file to display', metavar="FILE"
        )

        self.parser.add_argument(
            '-n', '--lines', metavar="N", type=int, default=10, help="number of lines to display"
        )

        self.parser.add_argument(
            '-f', '--follow', help="continue to output as file grows", action='store_true'
        )

        super(TailCommand, self).__init__(
            name=name, usage=self.parser.format_help(), topic=topic,
            brief=brief, **kwargs
        )

    def run(self, shell, args, ctx):
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

    def complete(self, shell, args, prefix):
        return path_completer(shell, args, prefix)

    def tail(self, fname, lines=10, block_size=1024):
        data = []
        blocks = -1
        num_lines = 0
        where = 0

        with open(fname) as fp:
            # seek to the end and get the number of bytes in the file
            fp.seek(0,2)
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
                    fp.seek(0,0)
                    # read data
                    data.insert(0, fp.read(num_bytes))
                num_lines = data[0].count('\n')
                bytes_left -= block_size
                blocks -= 1
                
            return ''.join(data).splitlines()[-lines:]


    def follow_file(self, fname):
        with open(fname) as fp:
            # jump to the end of the file
            fp.seek(0,2)
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
