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
Windows specific functions
'''

import os
import sys
import re


__all__ = [
    'find_bins_in_path',
    'is_path_prefix',
    'path_completer',
    'Win32AnsiStream'
]


def is_exe(path):
    (name, ext) = os.path.splitext(path)
    return (
        os.isfile(path) and
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
        for entry in os.listdir(path):
            p = os.path.join(path, entry)
            if os.path.isfile(p):
                name, ext = os.path.splitext(entry)
                if ext.lower() in ('.exe', '.bat'):
                    bins.add(name)
    return bins


def path_completer(path):
    path = path.replace('/', '\\')

    if not is_path_prefix(path):
        path = '.\\' + path

    if path.endswith('\\'):
        root = path[:-1] or '\\'
        prefix = ''
    else:
        root = os.path.dirname(path)
        prefix = os.path.basename(path)

    if not os.path.isdir(root):
        return []

    files = []
    dirs = []
    for entry in os.listdir(root):
        full = os.path.join(root, entry)
        if not prefix or entry.startswith(prefix):
            if os.path.isdir(full):
                dirs.append(entry + '\\')
            else:
                files.append(entry)
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



ANSI_CODE_MAP = {
    '0;30m': 0x0,             #black
    '0;31m': 0x4,             #red
    '0;32m': 0x2,             #green
    '0;33m': 0x4+0x2,         #brown?
    '0;34m': 0x1,             #blue
    '0;35m': 0x1+0x4,         #purple
    '0;36m': 0x2+0x4,         #cyan
    '0;37m': 0x1+0x2+0x4,     #grey
    '1;30m': 0x1+0x2+0x4,     #dark gray
    '1;31m': 0x4+0x8,         #red
    '1;32m': 0x2+0x8,         #light green
    '1;33m': 0x4+0x2+0x8,     #yellow
    '1;34m': 0x1+0x8,         #light blue
    '1;35m': 0x1+0x4+0x8,     #light purple
    '1;36m': 0x1+0x2+0x8,     #light cyan
    '1;37m': 0x1+0x2+0x4+0x8, #white
    '0m': None
}

ANSI_CODE_RE = re.compile('\x1b\\[([0-9;]+[HJm])')


class Win32AnsiStream(object):

    def __init__(self, stream):
        self.stream = stream
        self._win32_initial_attrs = None

    def write(self, data):
        print(repr(data), file=sys.stderr)
        start = 0
        in_code = False
        for chunk in ANSI_CODE_RE.split(data):
            if chunk:
                if in_code:
                    code = ANSI_CODE_MAP.get(chunk)
                    if code:
                        self.stream.write('<' + hex(code) + '>')
                    elif chunk == '0m':
                        # reset
                        pass
                else:
                    self.stream.write(chunk)
            in_code = not in_code

        return len(data)

    def __getattr__(self, attr):
        return getattr(self.stream, attr)
