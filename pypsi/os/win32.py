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

__all__ = [
    'find_bins_in_path',
    'is_path_prefix',
    'path_completer'
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
