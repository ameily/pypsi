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

from pypsi.base import Command, PypsiArgParser
import os

TailCmdUsage = "%(prog)s [-n] [-f] [-h] file"


class TailCommand(Command):
    '''
    Displays the last N lines of a file to the screen.
    '''

    def __init__(self, name='tail', topic='shell', **kwargs):
        self.parser = PypsiArgParser(
            prog=name,
            description='display last N lines of a file',
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

        super(TailCommand, self).__init__(name=name, usage=self.parser.format_help(),
                                          topic=topic, brief='display last N lines of a file',
                                          **kwargs)

    def run(self, shell, args, ctx):
        ns = self.parser.parse_args(shell, args)
        if self.parser.rc is not None:
            return self.parser.rc

        # check for valid input file
        if not os.path.isfile(ns.input_file):
            self.error(shell, "invalid file path: ", ns.input_file, "\n")
            return -1

        # get number of lines, determine how many to display/skip
        with open(ns.input_file) as fp:
            num_lines = sum(1 for line in fp)
            
        lines_to_print = min(num_lines, ns.lines)
        lines_to_skip = 0
        if lines_to_print < num_lines:
            lines_to_skip = num_lines - lines_to_print

        # print the appropriate lines from the file
        if not ns.follow:
            idx = 1
            with open(ns.input_file) as fp:
                for line in fp:
                    if idx > lines_to_skip:
                        print(line, end='', flush=True)
                    else:
                        idx += 1
                print()
        # watch the file and print as necessary
        else:
            self.watch_file(ns.input_file, lines_to_skip)

        return 0

    def watch_file(self, fname, skip):
        idx = 1
        with open(fname) as fp:
            try:
                while 1:
                    where = fp.tell()
                    line = fp.readline()
                    if not line:
                        fp.seek(where)
                    else:
                        if idx > skip:
                            print(line, end='', flush=True)
                        else:
                            idx += 1
            except (KeyboardInterrupt):
                print()
                return 0
                
        return 0
