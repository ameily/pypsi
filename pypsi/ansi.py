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
from types import ModuleType
from typing import Any, Iterator, TextIO, Union
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
    white = '\x1b[37m'
    fg_reset = '\x1b[39m'

    bright_red = '\x1b[1;31m'
    bright_green = '\x1b[1;32m'
    bright_yellow = '\x1b[1;33m'
    bright_blue = '\x1b[1;34m'
    bright_magenta = '\x1b[1;35m'
    bright_cyan = '\x1b[1;36m'
    bright_white = '\x1b[1;37m'

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
    ansi_start = s.find('\x1b[')
    ansi_end = None
    while ansi_start >= 0:
        ansi_end = ansi_start
        while ansi_end < length and s[ansi_end] not in 'ABCDEFGHJKSTfmnsulh\r\n':
            ansi_end += 1
        length -= (ansi_end - ansi_start) + 1
        ansi_start = s.find('\x1b[', ansi_end)
    return length


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


def wrap(s: str, ansi: bool = True, **kwargs) -> Iterator[str]:
    '''
    Word-wrap a string.
    '''
    kwargs.setdefault('replace_whitespace', False)
    kwargs.setdefault('drop_whitespace', False)
    tw_wrap = ansi_textwrap.wrap if ansi else textwrap.wrap
    for line in s.splitlines(keepends=True):
        yield from tw_wrap(line, **kwargs)


class AnsiStream:

    def __init__(self, stream: TextIO, width: int = -1):
        self.stream = stream
        if width < 0 and stream.isatty():
            self.detect_width()
        else:
            self._width = width

    def detect_width(self) -> None:
        try:
            self._width = os.get_terminal_size(self.stream.fileno()).columns
        except:
            self._width = 0

    def width(self) -> int:
        return self._width

    def __getattr__(self, name: str) -> Any:
        return getattr(self.stream, name)



def pypsi_print(*items, file: Union[TextIO, AnsiStream] = None, sep: str = None,
                flush: bool = False, end: str = os.linesep):
    file = file or sys.stdout
    if isinstance(file, AnsiStream):
        width = file.width()
        ansi = True
        file = file.stream
    else:
        width = 0
        ansi = False

    sep = sep or ''
    if ansi:
        s = sep.join(items)
    else:
        s = ''.join(strip_ansi_codes(sep.join(items)))

    if end:
        s += end

    if width:
        for line in wrap(s, width=width, ansi=ansi):
            print(line, file=file, end=None)
    else:
        print(s, file=file, end=None)

    if flush:
        file.flush()

