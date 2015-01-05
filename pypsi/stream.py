#
# .opyright (c) 2014, Adam Meily
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
from pypsi.format import get_lines, wrap_line

'''
Stream classes for writing to files.
'''


class AnsiCode(object):
    '''
    A single ansi escape code.
    '''

    def __init__(self, code, s=None):
        '''
        :param str code: the ansi escape code, usually begins with '\\x1b['
        :param str s: the body of the code, only useful if wrapping a string in
            this code
        '''
        self.code = code
        self.s = s

    def prompt(self):
        '''
        Wrap non-print-able characters in readline non visible markers. This is
        required if the string is going to be passed into :meth:`input`.
        '''
        return "\x01" + self.code + "\x02" + (self.s or '')

    def __str__(self):
        return self.code

    def __call__(self, s, postfix='\x1b[0m'):
        '''
        Wrap a given string in the escape code. This is useful for printing a
        word or sentence in a specific color.

        :param str s: the input string
        :param str postfix: the postfix string to (default is the ansi reset
            code)
        '''
        return AnsiCode(self.code, s + (postfix or ''))


class AnsiCodesSingleton(object):
    '''
    Holds all supported ansi escape codes.
    '''

    def __init__(self):
        #: Reset terminal color and style
        self.reset = AnsiCode('\x1b[0m')
        #: Gray
        self.gray = AnsiCode('\x1b[1;30m')
        #: Red (bold)
        self.red = AnsiCode('\x1b[1;31m')
        #: Green (bold)
        self.green = AnsiCode('\x1b[1;32m')
        #: Yellow (bold)
        self.yellow = AnsiCode('\x1b[1;33m')
        #: Blue (bold)
        self.blue = AnsiCode('\x1b[1;34m')
        #: Purple (bold)
        self.purple = AnsiCode('\x1b[1;35m')
        #: Cyan (bold)
        self.cyan = AnsiCode('\x1b[1;36m')
        #: White (bold)
        self.white = AnsiCode('\x1b[1;37m')
        #: Black
        self.black = AnsiCode('\x1b[0;30m')
        #: Clear the screen
        self.clear_screen = AnsiCode('\x1b[2J\x1b[;H')
        #: Underline text
        self.underline = AnsiCode('\x1b[4m')

        #: all codes as a dict, useful for formatting an ansi string
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

#: Global instance for all supported ansi codes (instance of
#: :class:`AnsiCodesSingleton`)
AnsiCodes = AnsiCodesSingleton()


def pypsi_print(*args, sep=' ', end='\n', file=None, flush=True, width=None, wrap=True):
    '''
    Wraps the functionality of the Python builtin `print` function. The
    :meth:`pypsi.shell.Shell.bootstrap` overrides the Python :meth:`print`
    function with :meth:`pypsi_print`.

    :param str sep: string to print between arguments
    :param str end: string to print at the end of the output
    :param file file: output stream, if this is :const:`None`, the default is
        :data:`sys.stdout`
    :param bool flush: whether to flush the output stream
    :param int width: override the stream's width
    :param bool wrap: whether to word wrap the output
    '''
    file = file or sys.stdout
    last = len(args) - 1

    if wrap and hasattr(file, 'width') and file.width:
        width = width or file.width
        parts = []
        for arg in args:
            if isinstance(arg, str):
                parts.append(arg)
            elif arg is None:
                parts.append('')
            elif isinstance(arg, AnsiCode):
                if file.isatty():
                    parts.append(str(arg))
            else:
                parts.append(str(arg))

        txt = sep.join(parts)
        lineno = 0
        for (line, endl) in get_lines(txt):
            #file.write("Line: "+line+' ['+str(endl)+']\n')
            if line:
                first = True
                wrapno = 0
                for wrapped in wrap_line(line, width):
                    if not wrapped:
                        continue
                    #file.write("Wrapped: '" + wrapped+"'\n")
                    wrapno += 1
                    if not first:
                        file.write('\n')
                    else:
                        first = False
                    file.write(wrapped)
            
            if not line or endl:
                #file.write("NO Line\n")
                file.write('\n')
    else:
        last = len(args) - 1
        for (i, arg) in enumerate(args):
            file.write(str(arg))
            if sep and i != last:
                file.write(sep)

    if end:
        file.write(end)
    if flush:
        file.flush()




class AnsiStream(object):
    '''
    Enhanced file stream wrapper that includes the ability to:

    - redirect output to a new stream, while keeping a stack of redirections
    - reset to the initial stream (cancel all redirects)
    - format an ansi string

    The :meth:`pypsi.shell.Shell.bootstrap` wraps both :data:`sys.stdout` and
    :data:`sys.stderr` in an :class:`AnsiStream` instance.
    '''

    #: Ansi mode to rely on the stream's :meth:`file.isatty` function
    TTY = 0
    #: Ansi mode to force ansi support always on
    ForceOn = 1
    #: Ansi mode to force ansi support always off
    ForceOff = 2

    def __init__(self, stream, ansi_mode=0, width=80):
        '''
        :param file stream: the initial stream to wrap (should be either
            :data:`sys.stdout` or :data:`sys.stderr`)
        :param int ansi_mode: the mode to use when checking if the active stream
            supports ansi escape codes
        :param int width: the streams width, which is used by
            :meth:`pypsi_print` and :meth:`pypsi.format.wrap_line`
        '''
        self.stream = stream
        self.ansi_mode = ansi_mode
        self.redirects = []
        self.width = width

    '''
    def write(self):  #*args, sep=' ', end='\n', flush=True):
        #self.stream.write("write()\n")
        #return
        for arg in args:
            #self.stream.write(str(type(arg))+'\n')
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
    '''
    '''
    def write(self, arg):
        if isinstance(arg, str):
            self.stream.write(arg)
        elif isinstance(arg, AnsiCode):
            if self.isatty():
                self.stream.write(str(arg))
        elif arg is not None:
            self.stream.write(str(arg))
    '''


    def redirect(self, stream, width=0):
        '''
        Redirect output to a new output stream.

        :param file stream: new output stream
        :param int width: the stream's width (0 indicates that no word wrapping
            should take place)
        '''
        self.redirects.append((self.stream, self.width))
        self.stream = stream
        self.width = width

    def reset(self, state=None):
        '''
        Reset the active stream to a specific state or the initial stream.

        :param int state: the state to reset to, as returned by
            :meth:`get_state` or :const:`None` to reset to the initial stream
        '''
        if self.redirects:
            if state is not None:
                if state == 0:
                    self.reset()
                elif state < len(self.redirects):
                    self.redirects  = self.redirects[:state]
                    (self.stream, self.width) = self.redirects.pop()
            else:
                (self.stream, self.width) = self.redirects[0]
                self.redirects = []

    def isatty(self):
        '''
        Checks if the stream is a TTY (ie :data:`sys.stdout` or
        :data:`sys.stderr`). This method will rely on the active ansi_mode.
        '''
        if self.ansi_mode == AnsiStream.TTY:
            return self.stream.isatty()
        return self.ansi_mode == AnsiStream.ForceOn

    def close(self, was_pipe=False):
        '''
        Close and reset the active redirection.

        :param bool was_pipe: whether the redirection was a pipe, in which case
            the underlying file will not be closed
        '''
        if self.redirects:
            if not was_pipe:
                self.stream.close()
            (self.stream, self.width) = self.redirects.pop()

    def get_state(self):
        '''
        Get the state of the stream.

        :returns int: the state id
        '''
        return len(self.redirects)

    def __getattr__(self, name):
        return getattr(self.stream, name)

    def ansi_format(self, tmpl, **kwargs):
        '''
        Format a string that contains ansi code terms. This function allows
        the following string to be the color red:

        ``sys.stdout.ansi_format("{red}Hello, {name}{reset}", name="Adam")``

        The :data:`pypsi.format.AnsiCodesSingleton.codes` dict contains all
        valid ansi escape code terms. If the current stream does not support
        ansi escape codes, they are dropped from the template prior to printing.

        :param str tmpl: the string template
        '''
        atty = self.isatty()
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
        :meth:`AnsiCode.prompt` for each code.
        '''
        atty = self.isatty()
        for (name, value) in kwargs.items():
            if isinstance(value, AnsiCode):
                kwargs[name] = value.prompt() if atty else ''

        for (name, code) in AnsiCodes.codes.items():
            kwargs[name] = code.prompt() if atty else ''

        return tmpl.format(**kwargs)
