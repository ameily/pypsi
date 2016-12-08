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
        end = "\x01{}\x02".format(self.end_code) if self.end_code else ''
        return "\x01{code}\x02{s}{end}".format(code=self.code, s=self.s or '',
                                               end=end)

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


def ansi_len(value):
    '''
    Get the length of the provided `str`, not counting any ansi codes.

    :param str value: the input string
    '''
    count = 0
    esc_code = False
    for c in value:
        if c == '\x1b':
            esc_code = True
        elif esc_code:
            if c in 'ABCDEFGHJKSTfmnsulh':
                esc_code = False
        else:
            count += 1
    return count


def ansi_center(s, width):
    '''
    Center the provided string for a given width.

    :param str s: the input string
    :param int width: the desired field width
    '''
    count = ansi_len(s)
    if count >= width:
        return s
    diff = (width - count) // 2
    space = (' '*diff)
    return space + s + space


def ansi_ljust(s, width):
    '''
    Left justify an input string, ensuring that it contains width charaters.

    :param str s: the input string
    :param int width: the desired output width
    :returns str: the output string
    '''
    count = ansi_len(s)
    if count >= width:
        return s
    diff = width - count
    return s + (' ' * diff)


def ansi_rjust(s, width):
    '''
    Right justify the input string.

    :param str s: the input string
    :param int width: the desired width
    :returns str: the output string
    '''
    count = ansi_len(s)
    if count >= width:
        return s
    diff = width - count
    return (' '*diff) + s
