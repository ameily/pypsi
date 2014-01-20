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


from pypsi.base import Plugin, Command
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

    def run(self, shell, args, ctx):
        if self.cmd_args == CmdArgsString:
            args = ' '.join(args)
        return self.func(args)


class CmdPlugin(Plugin):
    '''
    Wraps existing :mod:`cmd`-based shell commands to be pypsi compatible. This
    plugin is designed to ease the transition from the :mod:`cmd` module and
    isn't intended to be used in production. Tab completion is not supported for
    :mod:`cmd` commands.
    '''

    def __init__(self, cmd_args=CmdArgsList, **kwargs):
        '''
        :param int cmd_args: determines how the command arguments are passed to\
            the wrapped command (see :data:`CmdArgsList` and \
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
                #completer = None
                #if hasattr(shell, 'complete_'+cmd):
                #    completer = getattr(shell, 'complete_'+cmd)
                shell.register(CommandFunction(func, cmd_args=self.cmd_args, name=cmd, usage=usage))
        return 0

