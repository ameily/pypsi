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
import sys

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
    #return ['Root:' + root, 'Pref:' + prefix]
    #return ['Dirs:' + str(len(dirs)), 'files:' + str(len(files))]
    return dirs + files
    
