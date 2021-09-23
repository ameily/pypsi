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


import threading
import sys
import os
from contextlib import contextmanager
from typing import Text, TextIO, Any, Dict
from pypsi.os import make_ansi_stream


class ThreadLocalProxy:

    def __init__(self, target: Any):
        self.__target = target
        self.__proxies: Dict[int, Any] = {}

    def proxy(self, proxy: Any) -> None:
        self.__proxies[threading.get_ident()] = proxy or self.__target

    def unproxy(self) -> None:
        self.__proxies.pop(threading.get_ident(), None)

    def __call__(self) -> Any:
        return self.__proxies.get(threading.get_ident(), self.__target)

    def __getattr__(self, name: str) -> Any:
        target = self.__proxies.get(threading.get_ident(), self.__target)
        return getattr(target, name)


class InvocationThread(threading.Thread):
    '''
    An invocation of a command from the command line interface.
    '''

    def __init__(self, shell, invoke, stdin=None, stdout=None, stderr=None):
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

    def run(self):
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

    def stop(self):
        '''
        Attempt to stop the thread by explitily closing the stdin, stdout, and
        stderr streams.
        '''

        if self.is_alive():
            try:
                self.invoke.close_streams()
            except:
                pass
