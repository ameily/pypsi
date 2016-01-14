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

'''
Windows specific functions
'''

import os
import ctypes
import re
import msvcrt


def win32_path_completer(shell, args, prefix):
    root = None
    if args:
        root = args[-1]
        drive, root = os.path.splitdrive(root)
        if root:
            if not root.startswith(os.path.sep) and not root.startswith('.' + os.path.sep):
                root = '.' + os.path.sep + root
        else:
            root = '.' + os.path.sep
        root = os.path.join(drive, root)
    else:
        root = '.' + os.path.sep

    if root.endswith(prefix) and prefix:
        root = root[:0 - len(prefix)]

    #return ['prefix:'+prefix, 'root:'+root]

    if not os.path.exists(root):
        return []

    if os.path.isdir(root):
        files = []
        dirs = []
        prefix_lower = prefix.lower()
        for entry in os.listdir(root):
            full = os.path.join(root, entry)
            if entry.lower().startswith(prefix_lower):
                if os.path.isdir(full):
                    dirs.append(entry + os.path.sep)
                else:
                    files.append(entry)
        files = sorted(files)
        dirs = sorted(dirs)
        return dirs + files
    else:
        return []


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

    def __init__(self, stream):
        self.stream = stream
        self._win32_flush_pending = False

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

    def _win32_set_console_attrs(self, attrs):
        SetConsoleTextAttribute(self._win32_handle, attrs)
        self._win32_current_attrs = attrs

    def write(self, data):
        if not self._win32_handle:
            return self.stream.write(data)

        in_code = False
        for chunk in ANSI_CODE_RE.split(data):
            if chunk:
                if in_code:
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
                else:
                    self.stream.write(chunk)
                    self._win32_flush_pending = True
            in_code = not in_code
        return len(data)

    def flush(self):
        self.stream.flush()
        self._win32_flush_pending = False

    def __getattr__(self, attr):
        return getattr(self.stream, attr)


def make_ansi_stream(stream):
    '''
    Used by the Pypsi pipe line to create ANSI escape code compatible streams.
    '''
    if isinstance(stream, Win32AnsiStream):
        return stream
    return Win32AnsiStream(stream)
