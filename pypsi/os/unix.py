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
    'path_completer'
]


def find_bins_in_path():
    bins = set()
    paths = [x for x in os.environ['PATH'].split(':') if x.strip()]
    paths.append('./')
    for path in paths:
        path = path or './'
        for entry in os.listdir(path):
            p = os.path.join(path, entry)
            if os.path.isfile(p) and os.access(p, os.X_OK):
                bins.add(entry)
    return bins


def is_path_prefix(t):
    for prefix in ('./', '../', '/'):
        if t.startswith(prefix):
            return True
    return False


def path_completer(path):
    if not (path.startswith('/') or path.startswith('./')
            or path.startswith('../')):
        path = './' + path

    if path.endswith('/'):
        root = path[:-1] or '/'
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
                dirs.append(entry + '/')
            else:
                files.append(entry)
    files = sorted(files)
    dirs = sorted(dirs)
    return dirs + files
