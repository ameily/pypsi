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

from __future__ import annotations
from typing import TYPE_CHECKING, Callable, List, TextIO, Optional
import argparse
import sys

from . import completers
from .ansi import Color


if TYPE_CHECKING:
    from .shell import Shell
    from .cmdline import Token


TabCompletionMethod = Callable[['Shell', List[str], str], List[str]]


class Plugin:
    '''
    A plugin is an object that is able to modify a
    :py:class:`pypsi.shell.Shell` object's behavior. Whereas a command can be
    execute from user input, the `Plugin` class does not contain a `run()`
    function.
    '''

    def __init__(self, preprocess: int = None, postprocess: int = None):
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

    def setup(self, shell: Shell) -> None:  # pylint: disable=unused-argument
        '''
        Called after the plugin has been registered to the active shell.

        :param pypsi.shell.Shell shell: the active shell
        '''

    def on_input(self, shell: Shell, line: str) -> str:  # pylint: disable=unused-argument
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

    def on_tokenize(self, shell: Shell, tokens: List[Token], origin: str):
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
        # pylint: disable=unused-argument
        return tokens

    def on_input_canceled(self, shell: Shell):  # pylint: disable=unused-argument
        '''
        Called when the user can canceled entering a statement via SIGINT
        (Ctrl+C).

        :param pypsi.shell.Shell shell: the active shell
        '''

    def on_statement_finished(self, shell: Shell, rc: int):  # pylint: disable=unused-argument
        '''
        Called when a statement has been completely executed.

        :param pypsi.shell.Shell shell: the active shell
        :returns int: 0 on success, -1 on error
        '''


class Command:
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

    def __init__(self, name: str, usage: str = None, brief: str = None, topic: str = None,
                 pipe: str = 'str'):
        '''
        :param str name: the name of the command which the user will reference
            in the shell
        :param str usage: the usage message to be displayed to the user
        :param str brief: a brief description of the command
        :param str topic: the topic that this command belongs to
        :param str pipe: the type of data that will be read from and written to
            any pipes
        '''
        # pylint: disable=too-many-arguments
        self.name = name
        self.usage = usage or ''
        self.brief = brief or ''
        self.topic = topic or ''
        self.pipe = pipe or 'str'

    def complete(self, shell: Shell, args: List[str], prefix: str):  # pylint: disable=unused-argument
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

    def usage_error(self, *error: List[str]) -> None:
        '''
        Display an error message that indicates incorrect usage of this
        command. After the error is displayed, the usage is printed.

        :param pypsi.shell.Shell shell: the active shell
        :param args: list of strings that are the error message
        '''
        if error:
            self.error(*error)
        print(Color.bright_yellow(self.usage))

    def error(self, *error: List[str]) -> None:  # pylint: disable=unused-argument
        '''
        Display an error message to the user.

        :param pypsi.shell.Shell shell: the active shell
        :param args: the error message to display
        '''
        print(Color.bright_red(f'{self.name}: ', *error), file=sys.stderr)

    def run(self, shell: Shell, args: List[str]) -> int:
        '''
        Execute the command. All commands need to implement this method.

        :param pypsi.shell.Shell shell: the active shell
        :param list args: list of string arguments
        :returns int: 0 on success, less than 0 on error, and greater than 0 on
            invalid usage
        '''
        raise NotImplementedError()

    def setup(self, shell: Shell) -> None:  # pylint: disable=unused-argument
        '''
        Called when the plugin has been registered to the active shell.

        :param pypsi.shell.Shell shell: the active shell
        '''

    def fallback(self, shell: Shell, name: str, args: List[str]) -> int:  # pylint: disable=unused-argument
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
        return -1


class CommandShortCircuit(Exception):
    '''
    Exception raised when the user enter invalid arguments or requests usage
    information via the -h and --help flags.
    '''

    def __init__(self, code: int):
        '''
        :param int code: the code the command should return
        '''

        super().__init__(code)
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

        super().__init__(*args, **kwargs)

    def exit(self, status: int = 0, message: str = None) -> None:
        if message:
            print(Color.bright_red(message), file=sys.stderr)
        raise CommandShortCircuit(status)

    def print_usage(self, file: TextIO = None) -> None:
        f = file or sys.stderr
        print(Color.bright_yellow(self.format_usage()), file=f)

    def print_help(self, file: TextIO = None) -> None:
        f = file or sys.stderr
        print(Color.bright_yellow(self.format_help()), file=f)

    def get_options(self) -> List[str]:
        '''
        :return: All optional arguments (ex, '-v'/'--verbose')
        '''
        return list(self._op_completers.keys())

    def get_option_completer(self, option: str) -> TabCompletionMethod:
        '''
        Returns the callback for the specified optional argument,
        Or None if one was not specified.
        :param str option: The Option
        :return function: The callback function or None
        '''
        return self._op_completers.get(option, None)

    def has_value(self, arg: str) -> bool:
        '''
        Check if the optional argument has a value associated with it.
        :param str arg: Optional argument to check
        :return: True if arg has a value, false otherwise
        '''
        # pylint: disable=protected-access
        # _option_string_actions is a dictionary containing all of the optional
        # arguments and the argparse action they should perform. Currently, the
        # only two actions that store a value are _AppendAction/_StoreAction.
        # These represent the value passed to 'action' in add_argument:
        # parser.add_argument('-l', '--long', action='store')
        action = self._option_string_actions.get(arg, None)
        return isinstance(action, (argparse._AppendAction, argparse._StoreAction))

    def get_positional_completer(self, pos: int) -> Optional[TabCompletionMethod]:
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

    def get_positional_arg_index(self, args: List[str]) -> int:
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

    def add_subparsers(self, *args, **kwargs):
        kwargs.setdefault('parser_class', PypsiArgParser)
        return super().add_subparsers(*args, **kwargs)

    def add_argument(self, *args, completer: TabCompletionMethod = None, **kwargs):
        # pylint: disable=arguments-differ
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
        choices = kwargs.get('choices')

        if not cb and choices:
            cb = completers.choice_completer(choices)

        if not args or len(args) == 1 and args[0][0] not in chars:
            # If no positional args are supplied or only one is supplied and
            # it doesn't look like an option string, parse a positional
            # argument ( from argparse )
            if nargs and nargs in ('+', '*', argparse.REMAINDER):
                # Positional param can repeat
                # Currently only stores the last repeating completer specified
                self._repeating_cb = cb
            self._pos_completers.append(cb)
        else:
            # Add an optional argument
            for arg in args:
                self._op_completers[arg] = cb
        # Call argparse.add_argument()
        return super().add_argument(*args, **kwargs)

    def error(self, message: str) -> None:
        print(Color.bright_red(self.prog, ": error: ", message), file=sys.stderr)
        self.print_usage()
        self.exit(1)

    def complete(self, shell: Shell, args: List[str], prefix: str,
                 sub_parser: argparse._SubParsersAction = None) -> List[str]:
        '''
        Completion function that can tab complete options, options' values,
        and positional parameters. Shell, args, and prefix should be the same
        params as passed to the :meth:`pypsi.core.Command.complete` function

        :param parser: A PypsiArgParser object or an action object returned
            from :meth:`PypsiArgParser.add_subparsers`
        :param pypsi.shell.Shell shell: The current Shell object
        :param list args: The full list of current CLI args
        :param str prefix: The partial arg being completed
        :param bool case_sensitive: Whether the prefix will be completed
            in a case sensitive manner
        :return list: A list of possible options based on the prefix
        '''

        cmd_parser = None
        offset = 0
        completions = []
        ops = []

        choices = getattr(sub_parser, 'choices', None) if sub_parser else None

        if choices:
            # Is a subparser, get all possible subcommands
            sub_commands = list(choices)

            if len(args) == 1:
                # User is typing sub command
                completions.extend([x for x in sub_commands
                                    if x.startswith(prefix) or not prefix])
                return sorted(completions)

            # Get the command parser for the current subcommand
            cmd_parser = choices.get(args[0], None)
            offset = 1  # Set an offset so the subcmd is not counted in index
        else:
            # Is a PyPsiArgumentParser
            cmd_parser = self

        # Get the last complete argument - should always be the second to last
        # ['-s', 'tes<cursor>'] --or-- ['-s', 'test', '<cursor>']
        last_arg = args[-2] if len(args) >= 2 else ''

        if not cmd_parser:
            return []

        # Try to get an option's callback - returns None if no option or cb exists
        cb = cmd_parser.get_option_completer(last_arg)

        if callable(cb) and cmd_parser.has_value(last_arg):
            # If the option has a callback defined and has a value
            ops = cb(shell, args, prefix)
        elif prefix.startswith('-'):
            # Complete the optional arguments
            ops = cmd_parser.get_options()
        else:
            # Else complete the positional args

            # Get the current POSITIONAL index
            # This does NOT include any optional (-v --verbose OPTION) arguments
            index = cmd_parser.get_positional_arg_index(args)

            # Get the callback for the current positional parameter
            # Index includes subcmd if there is one, so subtract offset
            # Ex: 'cmd subcmd <cursor>' would have two args: ['subcmd', ''] but
            # 'cmd <cursor> would have one arg: ['']
            # Pass the params index here - if you want the first pos param, pass 0
            cb = cmd_parser.get_positional_completer(index - offset)
            if callable(cb):
                ops = cb(shell, args, prefix)

        if shell.profile.case_sensitive:
            completions.extend([o for o in ops
                                if not prefix or o.startswith(prefix)])
        else:
            completions.extend([o for o in ops if not prefix
                                or o.lower().startswith(prefix.lower())])
        return sorted(completions)
