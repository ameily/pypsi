#
# .opyright (c) 2014, Adam Meily
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

import sys
from pypsi.format import get_lines, wrap_line

'''
Stream classes for writing to files.
'''


class AnsiCode(object):
    '''
    A single ansi escape code.
    '''

    def __init__(self, code, s=None, end_code=None):
        '''
        :param str code: the ansi escape code, usually begins with '\\x1b['
        :param str s: the body of the code, only useful if wrapping a string in
            this code
        '''
        self.code = code
        self.s = s
        self.end_code = end_code

    def prompt(self):
        '''
        Wrap non-print-able characters in readline non visible markers. This is
        required if the string is going to be passed into :meth:`input`.
        '''
        #return "\x01" + self.code + "\x02" + (self.s or '')
        end = "\x01{}\x02".format(self.end_code) if self.end_code else ''
        return "\x01{code}\x02{s}{end}".format(code=self.code, s=self.s or '', end=end)

    def __str__(self):
        return self.code + (self.s or '') + (self.end_code or '')

    def __call__(self, s, postfix='\x1b[0m'):
        '''
        Wrap a given string in the escape code. This is useful for printing a
        word or sentence in a specific color.

        :param str s: the input string
        :param str postfix: the postfix string to (default is the ansi reset
            code)
        '''
        return AnsiCode(self.code, s, postfix)


class AnsiCodesSingleton(object):
    '''
    Holds all supported ansi escape codes.
    '''

    def __init__(self):
        #: Reset terminal color and style
        self.reset = AnsiCode('\x1b[0m')
        #: Gray
        self.gray = AnsiCode('\x1b[1;30m')
        #: Red (bold)
        self.red = AnsiCode('\x1b[1;31m')
        #: Green (bold)
        self.green = AnsiCode('\x1b[1;32m')
        #: Yellow (bold)
        self.yellow = AnsiCode('\x1b[1;33m')
        #: Blue (bold)
        self.blue = AnsiCode('\x1b[1;34m')
        #: Purple (bold)
        self.purple = AnsiCode('\x1b[1;35m')
        #: Cyan (bold)
        self.cyan = AnsiCode('\x1b[1;36m')
        #: White (bold)
        self.white = AnsiCode('\x1b[1;37m')
        #: Black
        self.black = AnsiCode('\x1b[0;30m')
        #: Clear the screen
        self.clear_screen = AnsiCode('\x1b[2J\x1b[;H')
        #: Underline text
        self.underline = AnsiCode('\x1b[4m')

        #: all codes as a dict, useful for formatting an ansi string
        self.codes = dict(
            reset=self.reset,
            gray=self.gray,
            red=self.red,
            green=self.green,
            yellow=self.yellow,
            blue=self.blue,
            purple=self.purple,
            cyan=self.cyan,
            white=self.white,
            black=self.black,
            clear_screen=self.clear_screen,
            underline=self.underline
        )

#: Global instance for all supported ansi codes (instance of
#: :class:`AnsiCodesSingleton`)
AnsiCodes = AnsiCodesSingleton()


def pypsi_print(*args, sep=' ', end='\n', file=None, flush=True, width=None, wrap=True):
    '''
    Wraps the functionality of the Python builtin `print` function. The
    :meth:`pypsi.shell.Shell.bootstrap` overrides the Python :meth:`print`
    function with :meth:`pypsi_print`.

    :param str sep: string to print between arguments
    :param str end: string to print at the end of the output
    :param file file: output stream, if this is :const:`None`, the default is
        :data:`sys.stdout`
    :param bool flush: whether to flush the output stream
    :param int width: override the stream's width
    :param bool wrap: whether to word wrap the output
    '''

    file = file or sys.stdout
    last = len(args) - 1

    if wrap and hasattr(file, 'width') and file.width:
        width = width or file.width
        parts = []
        for arg in args:
            if isinstance(arg, str):
                parts.append(arg)
            elif arg is None:
                parts.append('')
            elif isinstance(arg, AnsiCode):
                if file.isatty():
                    parts.append(str(arg))
            else:
                parts.append(str(arg))

        txt = sep.join(parts)
        lineno = 0
        for (line, endl) in get_lines(txt):
            #file.write("Line: "+line+' ['+str(endl)+']\n')
            if line:
                first = True
                wrapno = 0
                for wrapped in wrap_line(line, width):
                    if not wrapped:
                        continue
                    #file.write("Wrapped: '" + wrapped+"'\n")
                    wrapno += 1
                    if not first:
                        file.write('\n')
                    else:
                        first = False
                    file.write(wrapped)

            if not line or endl:
                #file.write("NO Line\n")
                file.write('\n')
    else:
        last = len(args) - 1
        for (i, arg) in enumerate(args):
            file.write(str(arg))
            if sep and i != last:
                file.write(sep)

    if end:
        file.write(end)
    if flush:
        file.flush()
