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

import os
import sys
import re
import ctypes
import msvcrt
import getpass


__all__ = [
    'find_bins_in_path',
    'is_path_prefix',
    'path_completer',
    'make_ansi_stream',
    'Win32AnsiStream'
]


def is_exe(path):
    (name, ext) = os.path.splitext(path)
    return (
        os.path.isfile(path) and
        ext.lower() in ('.exe', '.bat')
    )


def is_path_prefix(prefix):
    return (
        any([prefix.startswith(x) for x in ('\\', '.\\', '..\\')]) or (
            len(prefix) > 2 and prefix[1] == ':' and prefix[2] == '\\'
        )
    )


def find_bins_in_path():
    bins = set()
    paths = [x.strip() for x in os.environ['PATH'].split(';') if x.strip()]
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
        except:
            # The path doesn't exist
            pass

    return bins


def path_completer(path):
    path = path.replace('/', '\\')

    if not is_path_prefix(path):
        path = '.\\' + path

    if path.endswith('\\'):
        root = path
        prefix = ''
    elif path.endswith(':'):
        root = path + "\\"
        prefix = ''
    else:
        root = os.path.dirname(path)
        prefix = os.path.basename(path).lower()

    if not os.path.isdir(root):
        return []

    files = []
    dirs = []
    for entry in os.listdir(root):
        full = os.path.join(root, entry)
        if not prefix or entry.lower().startswith(prefix):
            if os.path.isdir(full):
                dirs.append(entry + '\\')
            else:
                files.append(entry + '\0')
    files = sorted(files)
    dirs = sorted(dirs)
    return dirs + files


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
    popen = subprocess.Popen

    def PopenWithLock(*args, **kwargs):
        with win32_popen_lock:
            child = popen(*args, **kwargs)
        return child

    subprocess.Popen = PopenWithLock

#: Map of ANSI escape color code to Windows Console text attribute
ANSI_CODE_MAP = {
    '0;30m': 0x0,              # black
    '0;31m': 0x4,              # red
    '0;32m': 0x2,              # green
    '0;33m': 0x4+0x2,          # brown?
    '0;34m': 0x1,              # blue
    '0;35m': 0x1+0x4,          # purple
    '0;36m': 0x2+0x4,          # cyan
    '0;37m': 0x1+0x2+0x4,      # grey
    '1;30m': 0x1+0x2+0x4,      # dark gray
    '1;31m': 0x4+0x8,          # red
    '1;32m': 0x2+0x8,          # light green
    '1;33m': 0x4+0x2+0x8,      # yellow
    '1;34m': 0x1+0x8,          # light blue
    '1;35m': 0x1+0x4+0x8,      # light purple
    '1;36m': 0x1+0x2+0x8,      # light cyan
    '1;37m': 0x1+0x2+0x4+0x8,  # white
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


class Win32AnsiStream(object):
    '''
    Windows stream wrapper that translates ANSI escape code to Windows Console
    API calls. Windows stream are not compatible with ANSI escape codes, so
    this class is a shim to provide transparent ANSI escape code support for
    Windows platforms.
    '''

    def __init__(self, stream, isatty=None, width=None):
        self.stream = stream
        self._win32_flush_pending = False
        self._isatty = isatty
        self.width = width

        try:
            self._win32_handle = msvcrt.get_osfhandle(stream.fileno())
        except:
            # stream is not a real File (ie. StringIO).
            self._win32_handle = None
            self._win32_console_initial_attrs = None
        else:
            csbi = CONSOLE_SCREEN_BUFFER_INFO()
            GetConsoleScreenBufferInfo(self._win32_handle, ctypes.byref(csbi))
            self._win32_console_initial_attrs = csbi.wAttributes
            self._win32_current_attrs = self._win32_console_initial_attrs

    def isatty(self):
        return self.stream.isatty() if self._isatty is None else self._isatty

    def _win32_set_console_attrs(self, attrs):
        SetConsoleTextAttribute(self._win32_handle, attrs)
        self._win32_current_attrs = attrs

    def write(self, data):
        if not self._win32_handle and self.isatty():
            return self.stream.write(data)

        in_code = False
        for chunk in ANSI_CODE_RE.split(data):
            if chunk:
                if in_code and self.isatty():
                    attrs = ANSI_CODE_MAP.get(chunk)
                    if attrs is None and chunk == '0m':
                        attrs = self._win32_console_initial_attrs

                    if attrs is not None:
                        if self._win32_flush_pending:
                            self.stream.flush()
                        # TODO we only handle foreground colors currently, so
                        # we mask the attributes to the bottom 4 bits. We
                        # should support background colors and other attributes
                        self._win32_set_console_attrs(
                            (self._win32_current_attrs & 0xfffffff0) | attrs
                        )
                elif not in_code:
                    self.stream.write(chunk)
                    self._win32_flush_pending = True
            in_code = not in_code
        return len(data)

    def flush(self):
        self.stream.flush()
        self._win32_flush_pending = False

    def __getattr__(self, attr):
        return getattr(self.stream, attr)

    def __eq__(self, other):
        if isinstance(other, Win32AnsiStream):
            return self.stream == other.stream
        else:
            return self.stream == other


def make_ansi_stream(stream, **kwargs):
    '''
    Used by the Pypsi pipe line to create ANSI escape code compatible streams.
    '''
    if isinstance(stream, Win32AnsiStream):
        return stream
    return Win32AnsiStream(stream, **kwargs)


def pypsi_win_getpass(prompt='Password: ', stream=None):
    import msvcrt
    import sys

    if not (stream or sys.stdin).isatty():
        return input(prompt)

    for c in prompt:
        msvcrt.putwch(c)
    pw = ""
    while 1:
        c = msvcrt.getwch()
        if c == '\r' or c == '\n':
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
