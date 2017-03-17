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


def command_completer(command, shell, args, prefix, case_sensitive=False):
    '''
    Completion function that can tab complete options,
    options' values, and positional paramaters.
    :param command: The action object returned from
                    PypsiArgParser.add_subparsers()
    :param shell:  The current Shell object
    :param args:   The full list of current CLI args
    :param prefix: The partial arg being completed
    :param case_sensitive: Whether the prefix will be completed
                           in a case sensitive manner
    :return: A list of possible options based on the prefix
    '''
    cmd_parser = None
    last_arg = None
    offset = 0
    completions = []
    ops = []

    # Try to get subcmd info - if it fails, assume no subcmds
    try:
        if len(args) == 1:
            # Get all possible subcmd's for the command
            base = [key for key in command.choices]
            completions.extend([x for x in base
                                if x.startswith(prefix) or not prefix])
            return sorted(completions)
        if command.choices:
            # Get the parser for the current subcmd
            cmd_parser = command.choices.get(args[0], None)
            offset = 1  # Set an offset so the subcmd is not counted in index
            last_arg = args[-2]
    except AttributeError:
        cmd_parser = command
        last_arg = args[-1]

    if not cmd_parser:
        return []

    # Try to get an option's callback - returns None if no option or cb exists
    cb = cmd_parser.get_option_callback(last_arg)

    if callable(cb) and cmd_parser.has_value(last_arg):
        # If the option has a value and has a callback defined
        ops = cb(shell, args, prefix)
    elif prefix.startswith('-'):
        ops = cmd_parser.get_options()
    else:
        # Else complete the positional args

        # Get the current POSITIONAL index
        # This does NOT include any optional (-j --job JOB) arguments
        index = cmd_parser.get_index(args)

        # Get the callback for the current positional parameter
        # Index includes subcmd if there is one, so subtract offset
        # Ex: 'job export <cursor>' would have two args: ['export', ''] but
        # 'use <cursor> would have one arg: ['']
        # Pass the pos. param # here - if you want the first pos param, pass 1
        cb = cmd_parser.get_positional_callback(index - offset)
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
