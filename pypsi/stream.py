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

import sys


'''
Stream classes for writing to files.
'''


class AnsiCode(object):

    def __init__(self, code, s=None):
        self.code = code
        self.s = s

    def __str__(self):
        return self.code

    def __call__(self, s, postfix='\x1b[0m'):
        return AnsiCode(self.code, s + (postfix or ''))


class AnsiCodesSingleton(object):

    def __init__(self):
        self.reset = AnsiCode('\x1b[0m')
        self.gray = AnsiCode('\x1b[1;30m')
        self.red = AnsiCode('\x1b[1;31m')
        self.green = AnsiCode('\x1b[1;32m')
        self.yellow = AnsiCode('\x1b[1;33m')
        self.blue = AnsiCode('\x1b[1;34m')
        self.purple = AnsiCode('\x1b[1;35)')
        self.cyan = AnsiCode('\x1b[1;36m')
        self.white = AnsiCode('\x1b[1;37m')
        self.black = AnsiCode('\x1b[0;30m')
        self.clear_screen = AnsiCode('\x1b[2J\x1b[;H')
        self.underline = AnsiCode('\x1b[4m')

        self.codes = dict(
            reset=self.reset,
            gray=self.gray,
            red=self.red,
            green=self.green,
            yellow=self.yellow,
            blue=self.blue,
            purple=self.purple,
            cyan=self.cyan,
            white=self.white,
            black=self.black,
            clear_screen=self.clear_screen,
            underline=self.underline
        )


AnsiCodes = AnsiCodesSingleton()


class AnsiStream(object):
    TTY = 0
    ForceOn = 1
    ForceOff = 2

    def __init__(self, stream, mode=TTY):
        self.stream = stream
        self.mode = mode
        self.redirects = []

    def write(self, *args, flush=True):
        for arg in args:
            if isinstance(arg, str):
                self.stream.write(arg)
            elif isinstance(arg, AnsiCode):
                if self.isatty():
                    self.stream.write(str(arg))
            elif arg is not None:
                self.stream.write(str(arg))

        if flush:
            self.stream.flush()

    def writeln(self, *args, flush=True):
        self.write(*args, flush=False)
        self.stream.write('\n')
        if flush:
            self.stream.flush()

    def redirect(self, stream):
        self.redirects.append(self.stream)
        self.stream = stream

    def reset(self, state=None):
        if self.redirects:
            if state is not None:
                if state == 0:
                    self.reset()
                elif state < len(self.redirects):
                    self.redirects  = self.redirects[:state]
                    self.stream = self.redirects.pop()
            else:
                self.stream = self.redirects[0]
                self.redirects = []

    def isatty(self):
        if self.mode == AnsiStream.TTY:
            return self.stream.isatty()
        return self.mode == AnsiStream.ForceOn

    def close(self, was_pipe=False):
        if self.redirects:
            if not was_pipe:
                self.stream.close()
            self.stream = self.redirects.pop()

    def get_state(self):
        return len(self.redirects)

    def __getattr__(self, name):
        return getattr(self.stream, name)
