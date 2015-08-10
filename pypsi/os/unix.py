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
Unix (Cygwin, Linux, etc) specific functions
'''

import os
import sys

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
    if not (path.startswith('/') or path.startswith('./') or path.startswith('../')):
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
    #return ['Root:' + root, 'Pref:' + prefix]
    #return ['Dirs:' + str(len(dirs)), 'files:' + str(len(files))]
    return dirs + files


'''
def unix_path_completer(shell, args, prefix):
    root = None
    if args:
        root = args[-1]
        if root:
            if not (root.startswith('/') or root.startswith('./') or root.startswith('../')):
                root = './' + root
        else:
            root = '.' + os.path.sep
    else:
        root = '.' + os.path.sep

    if prefix and root.endswith(prefix):
        root = root[:0 - len(prefix)]

    if not os.path.exists(root):
        return []

    if os.path.isdir(root):
        files = []
        dirs = []
        for entry in os.listdir(root):
            full = os.path.join(root, entry)
            if entry.startswith(prefix):
                if os.path.isdir(full):
                    dirs.append(entry + os.path.sep)
                else:
                    files.append(entry)
        files = sorted(files)
        dirs = sorted(dirs)
        return dirs + files
    else:
        return []

'''
