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


from pypsi.core import Plugin, Command
from io import StringIO
import sys

#: Keep command arguments as a list of strings
CmdArgsList = 0
#: Turn the list of arguments to a single string
CmdArgsString = 1


class CommandFunction(Command):
    '''
    Wraps a function as a pypsi command.
    '''

    def __init__(self, func, completer=None, cmd_args=CmdArgsList, **kwargs):
        '''
        :param callable func: the function to wrap
        :param int cmd_args: whether to keep the arguments as a list or convert
            them to a single string
        '''
        self.func = func
        self.completer = completer
        self.cmd_args = cmd_args
        super(CommandFunction, self).__init__(**kwargs)

    def run(self, shell, args):
        if self.cmd_args == CmdArgsString:
            args = ' '.join(args)
        return self.func(args)


class CmdPlugin(Plugin):
    '''
    Wraps existing :mod:`cmd`-based shell commands to be pypsi compatible. This
    plugin is designed to ease the transition from the :mod:`cmd` module and
    isn't intended to be used in production. Tab completion is not supported
    for :mod:`cmd` commands.
    '''

    def __init__(self, cmd_args=CmdArgsList, **kwargs):
        '''
        :param int cmd_args: determines how the command arguments are passed to
            the wrapped command (see :data:`CmdArgsList` and
            :data:`CmdArgsString`)
        '''
        self.cmd_args = cmd_args
        super(CmdPlugin, self).__init__(**kwargs)

    def get_help_message(self, shell, name, func):
        usage = ''
        if hasattr(shell, "help_"+name):
            stream = StringIO()
            (out, err) = sys.stdout, sys.stderr
            sys.stderr = sys.stdout = stream
            getattr(shell, "help_"+name)()
            (sys.stdout, sys.stderr) = out, err
            usage = stream.getvalue()
        elif func.__doc__:
            lines = []
            for line in func.__doc__.split('\n'):
                value = line.strip()
                if not value:
                    if lines:
                        lines.append('')
                else:
                    lines.append(line.strip())
            usage = '\n'.join(lines)
        return usage

    def setup(self, shell):
        '''
        Retrieves ``do_*()`` functions from the shell, parsing out help
        messages, generating :class:`FunctionCommand` wrappers, and registering
        the commands to the shell.
        '''
        for name in dir(shell):
            func = getattr(shell, name)
            if name.startswith('do_') and callable(func):
                cmd = name[3:]
                usage = self.get_help_message(shell, cmd, func)
                shell.register(
                    CommandFunction(func, cmd_args=self.cmd_args,
                                    name=cmd, usage=usage)
                )
        return 0
