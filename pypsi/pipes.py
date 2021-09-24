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


from __future__ import annotations
from typing import TYPE_CHECKING, Union, TextIO
import threading
import sys

if TYPE_CHECKING:
    from .shell import Shell
    from .cmdline import CommandInvocation


class InvocationThread(threading.Thread):
    '''
    An invocation of a command from the command line interface.
    '''

    def __init__(self, shell: Shell, invoke: CommandInvocation, stdin: Union[str, TextIO] = None,
                 stdout: Union[str, TextIO] = None, stderr: Union[str, TextIO] = None):
        '''
        :param pypsi.shell.Shell shell: the active shell.
        :param pypsi.cmdline.CommandInvocation invoke: the invocation to
            execute.
        :param stream stdin: override the invocation's stdin stream.
        :param stream stdout: override the invocation's stdout stream.
        :param stream stderr; override the invocation's stder stream.
        '''

        super().__init__()
        #: The active Shell
        self.shell = shell
        #: The :class:`~pypsi.cmdline.CommandInvocation` to execute.
        self.invoke = invoke
        #: Exception info, as returned by :meth:`sys.exc_info` if an exception
        #: occurred.
        self.exc_info = None
        #: The invocation return code.
        self.rc = None

        if stdin:
            self.invoke.stdin = stdin
        if stdout:
            self.invoke.stdout = stdout
        if stderr:
            self.invoke.stderr = stderr

    def run(self) -> None:
        '''
        Run the command invocation.
        '''

        try:
            self.rc = self.invoke(self.shell)
        except:
            self.exc_info = sys.exc_info()
            self.rc = None
        finally:
            pass

    def stop(self) -> None:
        '''
        Attempt to stop the thread by explitily closing the stdin, stdout, and
        stderr streams.
        '''

        if self.is_alive():
            try:
                self.invoke.close_streams()
            except:
                pass
