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

import sys
import os
from io import TextIOWrapper
from types import ModuleType
from typing import Any, Iterator, TextIO, Union, Tuple
import importlib.util
import textwrap
import builtins
from enum import Enum


class Color(Enum):
    '''
    ANSI escape code colors. The enum items can be used in multiple ways:

    .. highlight:: python

        >>> print(Color.red, 'hello world', Color.fg_reset, sep='')
        >>> print(Color.red('hello world'))
    '''
    black = '\x1b[30m'
    red = '\x1b[31m'
    green = '\x1b[32m'
    yellow = '\x1b[33m'
    blue = '\x1b[34m'
    magenta = '\x1b[35m'
    cyan = '\x1b[36m'
    gray = '\x1b[37m'
    fg_reset = '\x1b[39m'

    bright_red = '\x1b[1;31m'
    bright_green = '\x1b[1;32m'
    bright_yellow = '\x1b[1;33m'
    bright_blue = '\x1b[1;34m'
    bright_magenta = '\x1b[1;35m'
    bright_cyan = '\x1b[1;36m'
    white = '\x1b[1;37m'

    bg_black = '\x1b[40m'
    bg_red = '\x1b[41m'
    bg_green = '\x1b[42m'
    bg_yellow = '\x1b[43m'
    bg_blue = '\x1b[44m'
    bg_magenta = '\x1b[45m'
    bg_cyan = '\x1b[46m'
    bg_white = '\x1b[47m'
    bg_reset = '\x1b[49m'

    bright = '\x1b[1m'
    dim = '\x1b[2m'
    normal = '\x1b[22m'

    reset_all = '\x1b[0m'

    def __call__(self, *items) -> str:
        '''
        Wrap the string in the ANSI code, ending with the ``reset_all`` code.
        '''
        s = ''.join(str(i) for i in items)
        return f'{self}{s}{Color.reset_all}'

    def __str__(self) -> str:
        return self.value

    def __add__(self, other: Union[str, 'Color']) -> str:
        if isinstance(other, Color):
            return self.value + other.value
        if isinstance(other, str):
            return self.value + other
        raise TypeError(f'invalid operand types: Color and {type(other)}')

    @property
    def prompt(self) -> str:
        '''
        Enclose the escape code in the non-printable character marker, for use within a prompt.
        '''
        return f'\x01{self}\x02'


def ansi_clear_screen() -> None:
    '''
    Clear the screen.
    '''
    print('\x1b[2J\x1b[;H')



def load_textwrap() -> ModuleType:
    '''
    Load a copy of the textwrap module.
    '''
    spec = importlib.util.find_spec('textwrap')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def ansi_len(s: str) -> int:
    length = len(s)
    ansilen = length
    ansi_start = s.find('\x1b[')
    ansi_end = None
    while ansi_start >= 0:
        ansi_end = ansi_start
        while ansi_end < length and s[ansi_end] not in 'ABCDEFGHJKSTfmnsulh\r\n':
            ansi_end += 1
        ansilen -= (ansi_end - ansi_start) + 1
        ansi_start = s.find('\x1b[', ansi_end)
    return ansilen


def strip_ansi_codes(s: str) -> Iterator[str]:
    '''
    Strip ANSI escape codes from the string.
    '''
    start = 0
    length = len(s)
    ansi_start = s.find('\x1b[')
    while ansi_start >= 0:
        if start < ansi_start:
            yield s[start:ansi_start]

        start = ansi_start
        while start < length and s[start] not in 'ABCDEFGHJKSTfmnsulh':
            start += 1

        if s[start] not in '\r\n':
            start += 1

        ansi_start = s.find('\x1b[', start)

    if start < length:
        yield s[start:]


ansi_textwrap = load_textwrap()
ansi_textwrap.len = ansi_len
python_print = builtins.print


def split_line_ending(s: str) -> Tuple[str, str]:
    i = len(s) - 1
    while i >= 0:
        if not s[i].isspace():
            return (s[0:i+1], s[i+1:])
        i -= 1

    return ('', s)



def wrap(s: str, ansi: bool = True, **kwargs) -> Iterator[str]:
    '''
    Word-wrap a string.
    '''
    kwargs.setdefault('replace_whitespace', False)
    kwargs.setdefault('drop_whitespace', False)
    tw_wrap = ansi_textwrap.wrap if ansi else textwrap.wrap
    for line in s.splitlines(keepends=True):
        line, end = split_line_ending(line)
        if line:
            yield from (wrapped.strip() + end for wrapped in tw_wrap(line, **kwargs))
        else:
            yield end


class AnsiStream(TextIOWrapper):

    def __init__(self, stream: TextIOWrapper, width: int = None, max_width: int = None,
                 ansi: bool = True):
        super().__init__(stream.buffer, encoding=stream.encoding, errors=stream.errors,
                         newline=None, line_buffering=stream.line_buffering,
                         write_through=stream.write_through)
        self.max_width = max_width
        self.ansi = ansi
        if width is None and stream.isatty():
            self.detect_width()
        else:
            self.width = width

    def detect_width(self) -> None:
        try:
            width = os.get_terminal_size(self.fileno()).columns - 1
            if self.max_width:
                width = min(width, self.max_width)
        except:
            width = 0

        self.width = width



def pypsi_print(*items, file: Union[TextIO, AnsiStream] = None, sep: str = None,
                flush: bool = False, end: str = os.linesep, word_wrap: bool = True):
    file = file or sys.stdout.thread_local_get()
    if isinstance(file, AnsiStream):
        width = file.width
        ansi = file.ansi
    else:
        width = 0
        ansi = False

    if sep is None:
        sep = ' '

    if ansi:
        s = sep.join(str(item) for item in items)
    else:
        s = ''.join(strip_ansi_codes(sep.join(str(item) for item in items)))

    if end:
        s += end

    if width and word_wrap:
        for line in wrap(s, width=width, ansi=ansi):
            python_print(line, file=file, end='')
    else:
        python_print(s, file=file, end='')

    if flush:
        file.flush()


def ansi_title(s: str, underline: str = '=') -> str:
    if len(underline) != 1:
        raise TypeError('underline must be a single character')

    line = underline * ansi_len(s)
    return f'{s}{os.linesep}{line}'


def ansi_align(s: str, alignment: str, width: int):
    length = ansi_len(s)
    if length >= width:
        return s

    if alignment == 'center':
        spacing = ' ' * ((width - length) // 2)
        return f'{spacing}{s}'

    spacing = ' ' * (width - length)
    if alignment == 'left':
        return f'{s}{spacing}'
    if alignment == 'right':
        return f'{spacing}{s}'

    raise TypeError(f'unrecgonized alignment: {alignment!r}, must be one of: left, right, center')
