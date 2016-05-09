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
from pypsi.ansi import AnsiCode, AnsiCodes
from pypsi.os import make_ansi_stream


class ThreadLocalStream(object):
    '''
    A stream wrapper that is thread-local. This class enables thread-based
    pipes by wrapping :attr:`sys.stdout`, :attr:`sys.stderr`, and
    :attr:`sys.stdin` and making access to them thread-local. This allows each
    thread to, potentially, each thread to write to a different stream.

    A single stream, such as stdout, is wrapped in Pypsi as such:

    stdout -> thread local stream -> os-specific ansi stream
    '''

    DefaultAnsiStreamKwargs = dict()

    def __init__(self, target, **kwargs):
        '''
        :param file target: the original target stream (typically either
            :attr:`sys.stdout`, :attr:`sys.stderr`, and :attr:`sys.stdin`).
        :param int width: the width of the stream in characters, this attribute
            determines if word wrapping is enabled and how wide the lines are.
        :param bool isatty: whether the underlying stream is a tty stream,
            which supports ANSI escape cdes.
        '''

        if ThreadLocalStream.DefaultAnsiStreamKwargs:
            kw = dict(ThreadLocalStream.DefaultAnsiStreamKwargs)
            kw.update(kwargs)
            kwargs = kw

        self._target = make_ansi_stream(target, **kwargs)
        self._proxies = {}

    def _get_target(self):
        '''
        Get the target tuple for the current thread.

        :returns tuple: (target, width, isatty).
        '''

        return self._proxies.get(threading.current_thread().ident,
                                 self._target)

    def __getattr__(self, name):
        return getattr(self._get_target(), name)

    def __hasattr__(self, name):
        attrs = ('_proxy', '_unproxy', '_get_target', '_proxies', '_target')
        return name in attrs or hasattr(self._get_target(), name)

    def _proxy(self, target, **kwargs):
        '''
        Set a thread-local stream.

        :param file target: the target stream.
        :param int width: the stream width, in characters.
        :param bool isatty: whether the target stream is a tty stream.
        '''

        self._proxies[threading.current_thread().ident] = make_ansi_stream(
            target, **kwargs
        )

    def _unproxy(self, ident=None):
        '''
        Delete the proxy for a thread.

        :param int ident: the thread's :attr:`~threading.Thread.ident`
            attribute, or :const:`None` if the current thread's  proxy is being
            deleted.
        '''

        ident = ident or threading.current_thread().ident
        if ident in self._proxies:
            del self._proxies[ident]

    def ansi_format(self, tmpl, **kwargs):
        '''
        Format a string that contains ansi code terms. This function allows
        the following string to be the color red:

        ``sys.stdout.ansi_format("{red}Hello, {name}{reset}", name="Adam")``

        The :data:`pypsi.ansi.AnsiCodesSingleton.codes` dict contains all
        valid ansi escape code terms. If the current stream does not support
        ansi escape codes, they are dropped from the template prior to
        printing.

        :param str tmpl: the string template
        '''

        atty = self._get_target().isatty()
        for (name, value) in kwargs.items():
            if isinstance(value, AnsiCode):
                kwargs[name] = str(value) if atty else ''

        for (name, code) in AnsiCodes.codes.items():
            kwargs[name] = code.code if atty else ''

        return tmpl.format(**kwargs)

    def ansi_format_prompt(self, tmpl, **kwargs):
        '''
        Format a string that contains ansi code terms. This function allows
        performs the same formatting as :meth:`ansi_format`, except this is
        intended for formatting strings in prompt by calling
        :meth:`pypsi.ansi.AnsiCode.prompt` for each code.
        '''

        atty = self._get_target().isatty()
        for (name, value) in kwargs.items():
            if isinstance(value, AnsiCode):
                kwargs[name] = value.prompt() if atty else ''

        for (name, code) in AnsiCodes.codes.items():
            kwargs[name] = code.prompt() if atty else ''

        return tmpl.format(**kwargs)

    def render(self, parts, prompt=False):
        '''
        Render a list of objects as  single string. This method is the
        string version of the :meth:`print` method. Also, this method will
        honor the current thread's :meth:`isatty` when rendering ANSI escape
        codes.

        :param list parts: list of object to render.
        :param bool prompt: whether to render
            :class:`~pypsi.ansi.AnsiCode` objects as prompts or not.
        :returns str: the rendered string.
        '''
        r = []
        target = self._get_target()
        for part in parts:
            if isinstance(part, AnsiCode):
                if target.isatty():
                    if prompt:
                        r.append(part.prompt())
                    else:
                        r.append(str(part))
                elif part.s:
                    r.append(part.s)
            else:
                r.append(str(part))
        return ''.join(r)


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

        super(InvocationThread, self).__init__()
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
