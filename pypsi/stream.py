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



class AnsiColorCodes(object):

    def __init__(self):
        self.reset = '\x1b[0m'
        self.gray = '\x1b[1;30m'
        self.red = '\x1b[1;31m'
        self.green = '\x1b[1;32m'
        self.yellow = '\x1b[1;33m'
        self.blue = '\x1b[1;34m'
        self.purple = '\x1b[1;35m'
        self.cyan = '\x1b[1;36m'
        self.white = '\x1b[1;37m'
        self.black = '\x1b[0;30m'

        self.codes = {
            'reset': self.reset,
            'gray': self.gray,
            'red': self.red,
            'green': self.green,
            'yellow': self.yellow,
            'blue': self.blue,
            'purple': self.purple,
            'cyan': self.cyan,
            'white': self.white,
            'black': self.black
        }

    def __getitem__(self, key):
        return self.codes[key]


class StdStreamProxy(object):

    def __init__(self, fp, colors=AnsiColorCodes()):
        self._colors = colors
        self._stack = fp if isinstance(fp, list) else [fp]

    @property
    def _fp(self):
        return self._stack[-1]

    def redirect(self, fp):
        self._stack.append(fp)

    def close(self, target=None):
        if len(self._stack) > 1:
            if target is None or target != self._fp:
                self._fp.close()
                self._stack.pop()

    def reset(self, fp):
        self._stack = fp if isinstance(fp, list) else [fp]
        while self._fp != fp and len(self._stack) > 1:
            self.close()
        self.close()

    def color_gray(self, *args):
        return self.colorize('gray', *args)

    def color_red(self, *args):
        return self.colorize('red', *args)

    def color_green(self, *args):
        return self.colorize('green', *args)

    def color_yellow(self, *args):
        return self.colorize('yellow', *args)

    def color_blue(self, *args):
        return self.colorize('blue', *args)

    def color_purple(self, *args):
        return self.colorize('purple', *args)

    def color_cyan(self, *args):
        return self.colorize('cyan', *args)

    def color_white(self, *args):
        return self.colorize('white', *args)

    def color_black(self, *args):
        return self.colorize('black', *args)

    def color_reset(self):
        return self.colorize('reset')

    def colorize(self, color, *args):
        #a = args
        #if self._fp.isatty():
        #    a.insert(0, self._colors[color])
        #    a.append(self._colors['reset'])
        #return a
        if self._fp.isatty():
            return self._colors[color]
        return ''

    def __getattr__(self, attr):
        return getattr(self._fp, attr)


class StdoutProxy(StdStreamProxy):

    def __init__(self, **kwargs):
        super(StdoutProxy, self).__init__(fp=sys.stdout, **kwargs)


class StderrProxy(StdStreamProxy):

    def __init__(self, **kwargs):
        super(StderrProxy, self).__init__(fp=sys.stderr, **kwargs)


class StdinProxy(StdStreamProxy):

    def __init__(self, **kwargs):
        super(StdinProxy, self).__init__(fp=sys.stdin, **kwargs)
