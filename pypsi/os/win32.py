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
Windows specific functions and classes.
'''

from io import TextIOWrapper
import os
import sys
import re
import ctypes
import msvcrt  # pylint: disable=import-error
import getpass


__all__ = [
    'find_bins_in_path',
    'is_path_prefix',
    'make_ansi_stream'
]


def is_exe(path):
    (_, ext) = os.path.splitext(path)
    return (
        os.path.isfile(path) and
        ext.lower() in ('.exe', '.bat')
    )


def is_path_prefix(prefix):
    return prefix.startswith(('\\', '.\\', '..\\')) or (
        len(prefix) > 2 and prefix[1] == ':' and prefix[2] == '\\'
    )


def find_bins_in_path():
    bins = set()
    paths = [x for x in os.environ.get('PATH', '').split(';') if x.strip()]
    paths.append('.\\')
    for path in paths:
        path = path or '.\\'
        try:
            for entry in os.listdir(path):
                p = os.path.join(path, entry)
                if os.path.isfile(p):
                    name, ext = os.path.splitext(entry)
                    if ext.lower() in ('.exe', '.bat'):
                        bins.add(name)
        except OSError:
            # The path doesn't exist
            pass

    return bins


if sys.platform == 'win32':
    #
    # HACK
    #
    # There is a race condition when calling Popen from multiple threads on
    # Windows. The problem is that Popen makes handles inheritable prior to
    # calling CreateProcess, which if Popen is being called simultaneously,
    # will cause undesired handles to leak into subprocesses. When dealing with
    # pipes, like Pypsi does, this is very problematic because processes
    # reading from stdin will not terminate since their stdin handle is still
    # open.
    #
    # The solution is to put a lock around calls to Popen. This way, creating
    # processes are essentially atomic and handles will not leak.
    #
    # More information can be found here: http://bugs.python.org/issue24909
    #

    import threading
    import subprocess

    win32_popen_lock = threading.Lock()
    popen_ctor = subprocess.Popen.__init__

    def PopenWithLock(*args, **kwargs):
        with win32_popen_lock:
            popen_ctor(*args, **kwargs)

    subprocess.Popen.__init__ = PopenWithLock


#: Map of ANSI escape color code to Windows Console text attribute
ANSI_CODE_MAP = {
    '0;30m': 0x0,                       # black
    '0;31m': 0x4,                       # red
    '0;32m': 0x2,                       # green
    '0;33m': 0x4 + 0x2,                 # brown?
    '0;34m': 0x1,                       # blue
    '0;35m': 0x1 + 0x4,                 # purple
    '0;36m': 0x2 + 0x4,                 # cyan
    '0;37m': 0x1 + 0x2 + 0x4,           # grey
    '1;30m': 0x1 + 0x2 + 0x4,           # dark gray
    '1;31m': 0x4 + 0x8,                 # red
    '1;32m': 0x2 + 0x8,                 # light green
    '1;33m': 0x4 + 0x2 + 0x8,           # yellow
    '1;34m': 0x1 + 0x8,                 # light blue
    '1;35m': 0x1 + 0x4 + 0x8,           # light purple
    '1;36m': 0x1 + 0x2 + 0x8,           # light cyan
    '1;37m': 0x1 + 0x2 + 0x4 + 0x8,     # white
    '0m': None
}

ANSI_CODE_RE = re.compile('\x1b\\[([0-9;]+[HJm])')

##############################################################################
#
# The following ctypes definitions and Windows DLL function were pulled from
# https://www.burgaud.com/bring-colors-to-the-windows-console-with-python/

SetConsoleTextAttribute = ctypes.windll.kernel32.SetConsoleTextAttribute
GetConsoleScreenBufferInfo = ctypes.windll.kernel32.GetConsoleScreenBufferInfo

SHORT = ctypes.c_short
WORD = ctypes.c_ushort


class COORD(ctypes.Structure):
    """struct in wincon.h."""
    _fields_ = [
        ("X", SHORT),
        ("Y", SHORT)
    ]


class SMALL_RECT(ctypes.Structure):
    """struct in wincon.h."""
    _fields_ = [
        ("Left", SHORT),
        ("Top", SHORT),
        ("Right", SHORT),
        ("Bottom", SHORT)
    ]


class CONSOLE_SCREEN_BUFFER_INFO(ctypes.Structure):
    """struct in wincon.h."""
    _fields_ = [
        ("dwSize", COORD),
        ("dwCursorPosition", COORD),
        ("wAttributes", WORD),
        ("srWindow", SMALL_RECT),
        ("dwMaximumWindowSize", COORD)
    ]

##############################################################################


class Win32AnsiStream(TextIOWrapper):
    '''
    Windows stream wrapper that translates ANSI escape code to Windows Console
    API calls. Windows stream are not compatible with ANSI escape codes, so
    this class is a shim to provide transparent ANSI escape code support for
    Windows platforms.
    '''

    def __init__(self, file: TextIOWrapper):
        super().__init__(file.buffer, encoding=file.encoding, errors=file.errors,
                         newline=None, line_buffering=file.line_buffering,
                         write_through=file.write_through)

        try:
            self._win32_handle = msvcrt.get_osfhandle(self.fileno())
        except OSError:
            # stream is not a real File (ie. StringIO).
            self._win32_handle = None
            self._win32_console_initial_attrs = None
        else:
            csbi = CONSOLE_SCREEN_BUFFER_INFO()
            GetConsoleScreenBufferInfo(self._win32_handle, ctypes.byref(csbi))
            self._win32_console_initial_attrs = csbi.wAttributes
            self._win32_current_attrs = self._win32_console_initial_attrs

        self._win32_flush_pending = False

    def _win32_set_console_attrs(self, attrs):
        SetConsoleTextAttribute(self._win32_handle, attrs)
        self._win32_current_attrs = attrs

    def write(self, data):
        if not self._win32_handle and self.isatty():
            return super().write(data)

        in_code = False
        for chunk in ANSI_CODE_RE.split(data):
            if chunk:
                if in_code and self.isatty():
                    attrs = ANSI_CODE_MAP.get(chunk)
                    if attrs is None and chunk == '0m':
                        attrs = self._win32_console_initial_attrs

                    if attrs is not None:
                        if self._win32_flush_pending:
                            self.flush()
                        # we only handle foreground colors currently, so
                        # we mask the attributes to the bottom 4 bits. We
                        # should support background colors and other attributes
                        self._win32_set_console_attrs(
                            (self._win32_current_attrs & 0xfffffff0) | attrs
                        )
                elif not in_code:
                    super().write(chunk)
                    self._win32_flush_pending = True
            in_code = not in_code
        return len(data)

    def flush(self):
        super().flush()
        self._win32_flush_pending = False


def make_ansi_stream(stream: TextIOWrapper, **kwargs) -> TextIOWrapper:
    '''
    Used by the Pypsi pipe line to create ANSI escape code compatible streams.
    '''
    if isinstance(stream, Win32AnsiStream):
        return stream
    return Win32AnsiStream(stream, **kwargs)


def pypsi_win_getpass(prompt='Password: ', stream=None):
    if not (stream or sys.stdin).isatty():
        return input(prompt)

    for c in prompt:
        msvcrt.putwch(c)
    pw = ""
    while 1:
        c = msvcrt.getwch()
        if c in ('\r', '\n'):
            break
        if c == '\003':
            raise KeyboardInterrupt
        if c == '\b':
            pw = pw[:-1]
        else:
            pw = pw + c
    msvcrt.putwch('\r')
    msvcrt.putwch('\n')
    return pw


if getpass.win_getpass is getpass.getpass:
    getpass.getpass = pypsi_win_getpass
