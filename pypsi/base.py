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

'''
Base classes for developing pluggable commands and plugins.
'''


import argparse
import sys
from pypsi.stream import AnsiCodes


class Plugin(object):
    '''
    A plugin is an object that is able to modify a :py:class:`pypsi.shell.Shell`
    object's behavior. Whereas a command can be execute from user input, the
    `Plugin` class does not contain a `run()` function.
    '''

    def __init__(self, preprocess=None, postprocess=None):
        '''
        Constructor can take two parameters: `preprocess` and `postprocess`. These
        values determine where the plugin resides inside of the preprocess and
        postprocess list. This list, inside of :class:`pypsi.shell.Shell`, is iterated
        sequentially, from most priority to least. So, the highest priority
        value is 0, which means it will be the first plugin to run, and the
        lowest value is 100, which means it will be the last plugin to run. If
        either value is `None`, the plugin is not added to the processing list.
        For example, if this plugin only provides a preprocessing functionality,
        then postprocess should be set to :const:`None`.

        :param int preprocess: the preprocess priority
        :param int postprocess: the postprocess priority
        '''
        self.preprocess = preprocess
        self.postprocess = postprocess

    def setup(self, shell):
        '''
        Called after the plugin has been registered to the active shell.

        :param pypsi.shell.Shell shell: the active shell
        :returns int: 0 on success, -1 on failure
        '''
        return 0

    def on_input(self, shell, line):
        '''
        Called after input from the user has been received. The return value is
        the preprocessed line. This means that modifying the line argument will
        not populate back. If this function does no preprocessing, return line
        unmodified.

        :param pypsi.shell.Shell shell: the active shell
        :param str line: the current input statement string
        :returns str: the preprocessed line
        '''
        return line

    def on_tokenize(self, shell, tokens, origin):
        '''
        Called after an input string has been tokenized. If this function
        performs no preprocessing, return the tokens unmodified.

        :param pypsi.shell.Shell shell: the active shell
        :param list tokens: the list of :class:`pypsi.cmdline.Token` objects
        :param str origin: the origin of the input, can be either 'input' if
            received from a call to `input()` or 'prompt' if the input is the
            prompt to display to the user
        :returns list: the list of preprocessed :class:`pypsi.cmdline.Token`
            objects
        '''
        return tokens

    def on_input_canceled(self, shell):
        '''
        Called when the user can canceled entering a statement via SIGINT
        (Ctrl+C).

        :param pypsi.shell.Shell shell: the active shell
        :returns int: 0 on success, -1 on error
        '''
        return 0

    def on_statement_finished(self, shell, rc):
        '''
        Called when a statement has been completely executed.

        :param pypsi.shell.Shell shell: the active shell
        :returns int: 0 on success, -1 on error
        '''
        return 0


class Command(object):
    '''
    A pluggable command that users can execute. All commands need to derive from
    this class. When a command is executed by a user, the command's :meth:`run`
    method will be called. The return value of the :meth:`run` method is used
    when processing forthcoming commands in the active statement. The return
    value must be an :class:`int` and follows the Unix standard: 0 on success,
    less than 0 on error, and greater than 0 given invalid input or incorrect
    usage.

    Each command has a topic associated with it. This topic can be referenced by
    commands such as :class:`pypsi.commands.help.HelpCommand` to categorize
    commands in help messages.

    A command can be used as a fallback handler by implementing the
    :meth:`fallback` method. This is similar to the :meth:`run` method, except
    that is accepts one more argument: the command name to execute that wasn't
    found by the shell. The return value of :meth:`fallback` holds the same
    purpose as the return value of :meth:`run`.

    By the time :meth:`run` is called, the system streams have been updated to
    point to the current file streams. This means that the statement context's
    system streams are the same as the global streams in the :mod:`sys` module.
    For example, to write to `stdout`, a command may perform any of the
    following in the :meth:`run` method, all of which are equivalent:

    - ``ctx.stdout.write("Hello\\n")``
    - ``sys.stdout.write("Hello\\n")``
    - ``print("Hello")``
    '''

    def __init__(self, name, usage=None, brief=None, topic=None, pipe='str'):
        '''
        :param str name: the name of the command which the user will reference
            in the shell
        :param str usage: the usage message to be displayed to the user
        :param str brief: a brief description of the command
        :param str topic: the topic that this command belongs to
        :param str pipe: the type of data that will be read from and written to
            any pipes
        '''
        self.name = name
        self.usage = usage or ''
        self.brief = brief or ''
        self.topic = topic or ''
        self.pipe = pipe or 'str'

    def complete(self, shell, args, prefix):
        '''
        Called when the user attempts a tab-completion action for this command.

        :param pypsi.shell.Shell shell: the active shell
        :param list args: the list of arguments, the last one containing the
                          cursor position
        :param str prefix: the prefix that all items returned must start with
        :returns list: the list of strings that could complete the current action
        '''
        return []

    def usage_error(self, shell, *args):
        '''
        Display an error message that indicates incorrect usage of this command.
        After the error is displayed, the usage is printed.

        :param pypsi.shell.Shell shell: the active shell
        :param args: list of strings that are the error message
        '''
        self.error(shell, *args)
        print(AnsiCodes.yellow, self.usage, AnsiCodes.reset, sep='')

    def error(self, shell, *args):
        '''
        Display an error message to the user.

        :param pypsi.shell.Shell shell: the active shell
        :param args: the error message to display
        '''
        msg = "{}: {}".format(self.name, ''.join([ str(a) for a in args]))
        print(AnsiCodes.red, msg, AnsiCodes.reset, file=sys.stderr, sep='')

    def run(self, shell, args, ctx):
        '''
        Execute the command. All commands need to implement this method.

        :param pypsi.shell.Shell shell: the active shell
        :param list args: list of string arguments
        :param pypsi.cmdline.StatementContext: the current statement context
        :returns int: 0 on success, less than 0 on error, and greater than 0 on
            invalid usage
        '''
        raise NotImplementedError()

    def setup(self, shell):
        '''
        Called when the plugin has been registered to the active shell.

        :param pypsi.shell.Shell shell: the active shell
        :returns int: 0 on success, -1 on error
        '''
        return 0

    def fallback(self, shell, name, args, ctx):
        '''
        Called when this command was set as the fallback command. The only
        difference between this and :meth:`run` is that this method accepts the
        command name that was entered by the user.

        :param pypsi.shell.Shell shell: the active shell
        :param str name: the name of the command to run
        :param list args: arguments
        :param pypsi.cmdline.StatementContext ctx: the active context
        :returns int: 0 on success, less than 0 on error, and greater than 0 on
            invalid usage
        '''
        return None



class CommandShortCircuit(Exception):
    '''
    Exception raised when the user enter invalid arguments or requests usage
    information via the -h and --help flags.
    '''

    def __init__(self, code):
        '''
        :param int code: the code the command should return
        '''

        super(CommandShortCircuit, self).__init__(code)
        self.code = code


class PypsiArgParser(argparse.ArgumentParser):
    '''
    Customized :class:`argparse.ArgumentParser` for use in pypsi. This class slightly
    modifies the base ArgumentParser so that the following occurs:

    - The whole program does not exit on printing the help message or bad
      arguments
    - Any error messages are intercepted and printed on the active shell's error
      stream
    '''

    def exit(self, status=0, message=None):
        if message:
            print(AnsiCodes.red, message, AnsiCodes.reset, file=sys.stderr, sep='')
        raise CommandShortCircuit(status)

    def print_usage(self, file=None):
        f = file or sys.stderr
        print(AnsiCodes.yellow, self.format_usage(), AnsiCodes.reset, sep='', file=f)

    def print_help(self, file=None):
        f = file or sys.stderr
        print(AnsiCodes.yellow, self.format_help(), AnsiCodes.reset, sep='', file=f)

    def error(self, message):
        print(AnsiCodes.red, self.prog, ": error: ", message, AnsiCodes.reset, sep='', file=sys.stderr)
        self.print_usage()
        self.exit(1)
