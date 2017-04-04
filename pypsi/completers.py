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
Builtin tab completion functions.
'''

from pypsi.os import path_completer  # noqa


def command_completer(parser, shell, args, prefix, case_sensitive=False):
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

    if hasattr(parser, 'choices'):
        # Is a subparser, get all possible subcommands
        sub_commands = [key for key in parser.choices]

        if len(args) == 1:
            # User is typing sub command
            completions.extend([x for x in sub_commands
                                if x.startswith(prefix) or not prefix])
            return sorted(completions)

        # Get the command parser for the current subcommand
        cmd_parser = parser.choices.get(args[0], None)
        offset = 1  # Set an offset so the subcmd is not counted in index
    else:
        # Is a PyPsiArgumentParser
        cmd_parser = parser

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

    if case_sensitive:
        completions.extend([o for o in ops
                            if not prefix or o.startswith(prefix)])
    else:
        completions.extend([o for o in ops if not prefix
                            or o.lower().startswith(prefix.lower())])
    return sorted(completions)


def choice_completer(choices, case_sensitive=False):
    '''
    Tab complete from a list of choices.

    :param list choices: the list of choices
    :param bool case_sensitive: whether the choices are case sensitive
    '''
    def complete(shell, args, prefix):
        r = []
        for choice in choices:
            if choice.startswith(prefix if case_sensitive else prefix.lower()):
                r.append(choice)
        return r
    return complete
