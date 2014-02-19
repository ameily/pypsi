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

class PypsiStream(object):
    '''
    Unbuffered file output stream. This class should be used primarily
    for writing to :data:`sys.stdout` or :data:`sys.stderr`. The stream allows
    for prefix and postfix strings to be written to the file before or after
    each call to :func:`write`. This can be useful when printing colors to the
    screen or the log levels of messages.

    The wrapped file object can be a callable object that returns a file
    object. This object will then be called once during each
    invocation of :func:`write` to retrieve the current output file object.
    '''

    def __init__(self, fobj, prefix=None, postfix=None):
        '''
        :param file fobj: the file object to wrap or a function to retrieve the
            file object when writing to it
        :param str prefix: a string to write to the stream whenever :func:`write`
            is called
        :param str postfix: a string to write to the stream after :func:`write`
            is called
        '''
        self.fobj = fobj
        self.prefix = prefix
        self.postfix = postfix

    def __call__(self, *args):
        '''
        Alias for :func:`write`.
        '''
        return self.write(*args)

    def write(self, *args):
        '''
        Write any number of arguments to the stream.
        '''
        stream = self.fobj if not callable(self.fobj) else self.fobj()
        if self.prefix:
            stream.write(self.prefix)

        for s in args:
            if isinstance(s, str):
                stream.write(s)
            elif s is not None:
                stream.write(str(s))

        if self.postfix:
            stream.write(self.postfix)

        stream.flush()


class AnsiStream(object):
    TTY = 0
    ForceOn = 1
    ForceOff = 2

    def __init__(self, mode=TTY):
        self.mode = mode
        self.codes = {
            'reset': '\x1b[0m',
            'gray': '\x1b[1;30m',
            'red': '\x1b[1;31m',
            'green': '\x1b[1;32m',
            'yellow': '\x1b[1;33m',
            'blue': '\x1b[1;34m',
            'purple': '\x1b[1;35m',
            'cyan': '\x1b[1;36m',
            'white': '\x1b[1;37m',
            'black': '\x1b[0;30m',
            'clear_screen': '\x1b[2J\x1b[;H'
        }

    def __getattr__(self, key):
        return self.__getitem__(key)

    def __getitem__(self, key):
        check = False
        if self.mode == self.TTY:
            check = self.isatty()
        elif self.mode == self.ForceOn:
            check = True
        elif self.mode == self.ForceOff:
            check = False

        return self.codes[key] if check else ''


class AnsiStdoutSingleton(AnsiStream):

    def isatty(self):
        return sys.stdout.isatty()


class AnsiStderrSingleton(AnsiStream):

    def isatty(self):
        return sys.stderr.isatty()


AnsiStdout = AnsiStdoutSingleton()
AnsiStderr = AnsiStderrSingleton()

