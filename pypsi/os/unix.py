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
Unix (Cygwin, Linux, etc) specific functions
'''

import os

__all__ = [
    'find_bins_in_path',
    'is_path_prefix',
    'make_ansi_stream',
    'UnixAnsiStream'
]


class UnixAnsiStream(object):

    def __init__(self, stream, width=None, isatty=None):
        self._stream = stream
        self.width = width
        self._isatty = isatty

    def isatty(self):
        return self._stream.isatty() if self._isatty is None else self._isatty

    def __getattr__(self, attr):
        return getattr(self._stream, attr)

    def __eq__(self, other):
        if isinstance(other, UnixAnsiStream):
            return self._stream == other.stream
        return self._stream == other


def make_ansi_stream(stream, **kwargs):
    '''
    Create an ANSI-code compatible file stream. Unix file streams support ANSI
    escape codes, so we don't need to do anything special.
    '''
    if isinstance(stream, UnixAnsiStream):
        return stream
    return UnixAnsiStream(stream, **kwargs)


def find_bins_in_path():
    bins = set()
    paths = [x for x in os.environ.get('PATH', '').split(':') if x.strip()]
    paths.append('./')
    for path in paths:
        path = path or './'
        try:
            for entry in os.listdir(path):
                p = os.path.join(path, entry)
                if os.path.isfile(p) and os.access(p, os.X_OK):
                    bins.add(entry)
        except:
            # bare except here because if this fails, tab completion can be entirely broken
            pass
    return bins


def is_path_prefix(t):
    for prefix in ('./', '../', '/'):
        if t.startswith(prefix):
            return True
    return False
