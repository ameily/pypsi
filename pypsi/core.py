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

'''
Base classes for developing pluggable commands and plugins.
'''


import argparse
import sys
from pypsi.ansi import AnsiCodes, AnsiCode
from pypsi.format import get_lines, wrap_line


class Plugin(object):
    '''
    A plugin is an object that is able to modify a
    :py:class:`pypsi.shell.Shell` object's behavior. Whereas a command can be
    execute from user input, the `Plugin` class does not contain a `run()`
    function.
    '''

    def __init__(self, preprocess=None, postprocess=None):
        '''
        Constructor can take two parameters: `preprocess` and `postprocess`
        These values determine where the plugin resides inside of the
        preprocess and postprocess list. This list, inside of
        :class:`pypsi.shell.Shell`, is iterated sequentially, from most
        priority to least. So, the highest priority value is 0, which means it
        will be the first plugin to run, and the lowest value is 100, which
        means it will be the last plugin to run. If either value is `None`, the
        plugin is not added to the processing list. For example, if this plugin
        only provides a preprocessing functionality, then postprocess should be
        set to :const:`None`.

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
    A pluggable command that users can execute. All commands need to derive
    from this class. When a command is executed by a user, the command's
    :meth:`run` method will be called. The return value of the :meth:`run`
    method is used when processing forthcoming commands in the active
    statement. The return value must be an :class:`int` and follows the Unix
    standard: 0 on success, less than 0 on error, and greater than 0 given
    invalid input or incorrect usage.

    Each command has a topic associated with it. This topic can be referenced
    by commands such as :class:`pypsi.commands.help.HelpCommand` to categorize
    commands in help messages.

    A command can be used as a fallback handler by implementing the
    :meth:`fallback` method. This is similar to the :meth:`run` method, except
    that is accepts one more argument: the command name to execute that wasn't
    found by the shell. The return value of :meth:`fallback` holds the same
    purpose as the return value of :meth:`run`.

    By the time :meth:`run` is called, the system streams have been updated to
    point to the current file streams issued in the statement. For example, if
    the statement redirects standard out (:attr:`sys.stdout`) to a file, the
    destination file is automatically opened and :attr:`sys.stdout` is
    redirected to the opened file stream. Once the command has complete
    execution, the redirected stream is automatically closed and
    :attr:`sys.stdout` is set to its original stream.
    '''

    def __init__(self, name, usage=None, brief=None,
                 topic=None, parser=None, pipe='str'):
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
        :returns list: the list of strings that could complete the current
            action
        '''
        return []

    def usage_error(self, shell, *args):
        '''
        Display an error message that indicates incorrect usage of this
        command. After the error is displayed, the usage is printed.

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
        msg = "{}: {}".format(self.name, ''.join([str(a) for a in args]))
        print(AnsiCodes.red, msg, AnsiCodes.reset, file=sys.stderr, sep='')

    def run(self, shell, args):
        '''
        Execute the command. All commands need to implement this method.

        :param pypsi.shell.Shell shell: the active shell
        :param list args: list of string arguments
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

    def fallback(self, shell, name, args):
        '''
        Called when this command was set as the fallback command. The only
        difference between this and :meth:`run` is that this method accepts the
        command name that was entered by the user.

        :param pypsi.shell.Shell shell: the active shell
        :param str name: the name of the command to run
        :param list args: arguments
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
    Customized :class:`argparse.ArgumentParser` for use in pypsi. This class
    slightly modifies the base ArgumentParser so that the following occurs:

    - The whole program does not exit on printing the help message or bad
      arguments
    - Any error messages are intercepted and printed on the active shell's
      error stream
    - Adds the option to provide callbacks for tab-completing
      options and parameters
    '''

    def __init__(self, *args, **kwargs):
        #: Store callback functions for positional parameters
        self._pos_completers = []
        #: Store callback functions for optional arguments with values
        self._op_completers = {}
        #: If a positional argument can be specified more than once,
        #  store it's callback here and return it multiple times
        self._repeating_cb = None

        super(PypsiArgParser, self).__init__(*args, **kwargs)

    def exit(self, status=0, message=None):
        if message:
            print(AnsiCodes.red, message, AnsiCodes.reset, file=sys.stderr,
                  sep='')
        raise CommandShortCircuit(status)

    def print_usage(self, file=None):
        f = file or sys.stderr
        print(AnsiCodes.yellow, self.format_usage(), AnsiCodes.reset, sep='',
              file=f)

    def print_help(self, file=None):
        f = file or sys.stderr
        print(AnsiCodes.yellow, self.format_help(), AnsiCodes.reset, sep='',
              file=f)

    def get_options(self):
        '''
        :return: All optional arguments (ex, '-v'/'--verbose')
        '''
        return [key for key in self._op_completers]

    def get_option_completer(self, option):
        '''
        Returns the callback for the specified optional argument,
        Or None if one was not specified.
        :param str option: The Option
        :return function: The callback function or None
        '''
        return self._op_completers.get(option, None)

    def has_value(self, arg):
        '''
        Check if the optional argument has a value associated with it.
        :param str arg: Optional argument to check
        :return: True if arg has a value, false otherwise
        '''
        # _option_string_actions is a dictionary containing all of the optional
        # arguments and the argparse action they should perform. Currently, the
        # only two actions that store a value are _AppendAction/_StoreAction.
        # These represent the value passed to 'action' in add_argument:
        # parser.add_argument('-l', '--long', action='store')
        action = self._option_string_actions.get(arg, None)
        return isinstance(action,
                          (argparse._AppendAction, argparse._StoreAction))

    def get_positional_completer(self, pos):
        '''
        Get the callback for a positional parameter
        :param pos: index of the parameter - first param's index = 0
        :return: The callback if it exists, else None
        '''
        try:
            return self._pos_completers[pos]
        except IndexError:
            if self._repeating_cb:
                # A positional parameter is set to repeat
                return self._repeating_cb
            return None

    def get_positional_arg_index(self, args):
        '''
        Get the positional index of a cursor, based on
        optional arguments and positional arguments
        :param list args: List of str arguments from the Command Line
        :return:
        '''
        index = 0
        for token in args:
            if token in self._option_string_actions:
                # Token is an optional argument ( ex, '-v' / '--verbose' )
                if self.has_value(token):
                    # Optional Argument has a value associated with it, so
                    # reduce index to not count it's value as a pos param
                    index -= 1
            else:
                # Is a positional param or value for an optional argument
                index += 1

        # return zero-based index
        return index - 1

    def add_argument(self, *args, completer=None, **kwargs):
        '''
        Override add_argument function of argparse.ArgumentParser to
        handle callback functions.
        :param args:   Positional arguments to pass up to argparse
        :param function completer: Optional callback function for argument
        :param kwargs: Keywork arguments to pass up to argparse
        :return:
        '''
        cb = completer
        nargs = kwargs.get('nargs', None)
        chars = self.prefix_chars

        if not args or len(args) == 1 and args[0][0] not in chars:
            # If no positional args are supplied or only one is supplied and
            # it doesn't look like an option string, parse a positional
            # argument ( from argparse )
            if nargs and nargs in ['+', '*']:
                # Positional param can repeat
                # Currently only stores the last repeating completer specified
                self._repeating_cb = cb
            self._pos_completers.append(cb)
        else:
            # Add an optional argument
            for arg in args:
                self._op_completers[arg] = cb
        # Call argparse.add_argument()
        return super(PypsiArgParser, self).add_argument(*args, **kwargs)

    def error(self, message):
        print(AnsiCodes.red, self.prog, ": error: ", message, AnsiCodes.reset,
              sep='', file=sys.stderr)
        self.print_usage()
        self.exit(1)


def pypsi_print(*args, sep=' ', end='\n', file=None, flush=True, width=None,
                wrap=True, wrap_prefix=None):
    '''
    Wraps the functionality of the Python builtin `print` function. The
    :meth:`pypsi.shell.Shell.bootstrap` overrides the Python :meth:`print`
    function with ``pypsi_print``.

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
                elif arg.s is not None:
                    parts.append(str(arg.s))
            else:
                parts.append(str(arg))

        txt = sep.join(parts)
        for (line, endl) in get_lines(txt):
            if line:
                first = True
                wrapno = 0
                for wrapped in wrap_line(line, width, wrap_prefix=wrap_prefix):
                    if not wrapped:
                        continue

                    wrapno += 1
                    if not first:
                        file.write('\n')
                    else:
                        first = False
                    file.write(wrapped)

            if not line or endl:
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
