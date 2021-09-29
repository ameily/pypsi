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
Builtin tab completion functions.
'''

from __future__ import annotations
import os
import sys
from typing import TYPE_CHECKING, List, Callable, Union

if TYPE_CHECKING:
    from .shell import Shell



def _filename_startswith(filename: str, prefix: str):
    '''
    Check if filename begins with a prefix string. This method handles
    case sensitivity behaviors on Winodws and Linux.

    :param str filename: file name
    :param str prefix: prefix string to check for
    :returns bool: the filename begins with the prefix string
    '''
    if sys.platform == 'win32':
        return filename.lower().startswith(prefix.lower())
    return filename.startswith(prefix)


def choice_completer(choices: List[str]) -> Callable[[Shell, List[str], str]]:
    '''
    Tab complete from a list of choices.

    :param list choices: the list of choices
    :param bool case_sensitive: whether the choices are case sensitive
    '''
    def complete(shell: Shell, args: List[str], prefix: str):  # pylint: disable=unused-argument
        r = []
        if not shell.profile.case_sensitive:
            prefix = prefix.lower()
            available = [choice.lower() for choice in choices]
        else:
            available = choices

        for choice in available:
            if choice.startswith(prefix):
                r.append(choice)
        return r
    return complete


def path_completer(shell: Shell, token: Union[List[str], str], prefix: str = '') -> List[str]:
    '''
    Tab complete a path, handles both Windows and Linux paths.
    '''
    # pylint: disable=unused-argument
    choices = []
    if isinstance(token, list):
        token = token[-1] if token else ''

    if not token:
        cwd = '.' + os.path.sep
        filename_prefix = ''
    elif len(token) > 1 and token[-1] == os.path.sep:
        cwd = os.path.expanduser(token[:-1] or os.path.sep)
        filename_prefix = ''
    else:
        filename_prefix = os.path.basename(token)
        cwd = os.path.expanduser(os.path.dirname(token) or '.' + os.path.sep)

    if not os.path.exists(cwd):
        return []

    if not os.path.isdir(cwd):
        return []

    for filename in os.listdir(cwd):
        if not _filename_startswith(filename, filename_prefix):
            continue

        if os.path.isdir(os.path.join(cwd, filename)):
            filename += os.path.sep
        else:
            filename += '\0'

        choices.append(prefix + filename[len(filename_prefix):])

    return choices
