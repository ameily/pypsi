#
# Copyright (c) 2021, Adam Meily <meily.adam@gmail.com>
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


import sys
from typing import List, Dict
from pypsi.ansi import ansi_title
from pypsi.plugins.block import BlockCommand
from pypsi.core import Command, PypsiArgParser, CommandShortCircuit
from pypsi.table import Table
from pypsi.shell import Shell


class Macro(Command):
    '''
    Recorded macro that executes statements sequentially. If the
    :class:`pypsi.plugins.variable.VariablePlugin` is registered, arguments
    passed in when the macro is called are translated into variables, ala Bash.
    Each statement may then reference the arguments via the variables ``$1-9``.
    The variable ``$0`` is the name of the macro. For example, the following
    statement would produce the corresponding variables:

    ``hello arg1 "arg 2" arg3``
    - ``$0`` = "hello"
    - ``$1`` = "arg1"
    - ``$2`` = "arg 2"
    - ``$3`` = "arg3"

    Once the macro has finished executing, the variables are argument variables
    are removed.
    '''

    def __init__(self, lines: List[str], **kwargs):
        super().__init__(**kwargs)
        self.lines = lines

    def run(self, shell: Shell, args: List[str]) -> int:
        rc = None

        with shell.ctx.vars as env:
            env += self._get_variables(args)
            for line in self.lines:
                rc = shell.execute(line)

        return rc

    def _get_variables(self, args: List[str]) -> dict:
        variables = {str(i): arg for i, arg in enumerate(args, start=1)}
        variables['0'] = self.name
        return variables


class MacroCommand(BlockCommand):
    '''
    Record and execute command macros. Macros can consist of one or more
    command statements. Macros are comparable to Bash functions. Once a macro
    has been recorded, a new command is registered in the shell as an instance
    of a :class:`Macro`.

    This command requires the :class:`pypsi.plugins.block.BlockPlugin` plugin.
    '''

    def __init__(self, name='macro', topic='shell', macros: Dict[str, List[str]] = None, **kwargs):
        brief = "manage registered macros"
        self.parser = PypsiArgParser(prog=name, description=brief)

        self.parser.add_argument('-l', '--list', help='list all macros', action='store_true')
        self.parser.add_argument('-d', '--delete', help='delete macro', action='store_true')
        self.parser.add_argument('-s', '--show', help='print macro body', action='store_true')
        self.parser.add_argument('name', help='macro name', nargs='?', metavar='NAME',
                                 completer=self.complete_macros)

        super().__init__(name=name, usage=self.parser.format_help(), brief=brief, topic=topic,
                         **kwargs)
        self.base_macros = macros or {}

    def complete_macros(self, shell: Shell, args: List[str], prefix: str):
        # pylint: disable=unused-argument
        registered = list(shell.ctx.macros.keys())
        if not shell.profile.case_sensitive:
            registered = [item.lower() for item in registered]
            prefix = prefix.lower()

        return [item for item in registered if item.startswith(prefix)]

    def complete(self, shell: Shell, args: List[str], prefix: str) -> List[str]:
        # The command_completer function takes in the parser, automatically
        # completes optional arguments (ex, '-v'/'--verbose') or sub-commands,
        # and complete any arguments' values by calling a callback function
        # with the same arguments as complete if the callback was defined
        # when the parser was created.
        return self.parser.complete(shell, args, prefix)

    def setup(self, shell: Shell) -> None:
        if 'macros' not in shell.ctx:
            shell.ctx.macros = {}

        shell.ctx.recording_macro_name = None

        for name, lines in self.base_macros.items():
            self.add_macro(shell, name, lines)

    def run(self, shell: Shell, args: List[str]) -> int:
        # pylint: disable=too-many-return-statements
        try:
            ns = self.parser.parse_args(args)
        except CommandShortCircuit as e:
            return e.code

        rc = 0
        if ns.show:
            if ns.delete or ns.list:
                self.usage_error('-s/--show cannot be used with -d/--delete or -l/--list')
                return 1

            if not ns.name:
                self.usage_error('missing required argument: NAME')
                return 1

            rc = self.print_macro(shell, ns.name)
        elif ns.delete:
            if ns.list:
                self.usage_error('-d/--delete cannot be used with -l/--list')
                return 1

            if not ns.name:
                self.usage_error('missing required argument: NAME')
                return 1

            rc = self.delete_macro(shell, ns.name)
        elif ns.list:
            if ns.name:
                self.usage_error(f'unrecgonized argument: {ns.name}')
                return 1

            rc = self.print_macro_list(shell)
        elif ns.name:
            if ns.name in shell.commands.keys() and ns.name not in shell.ctx.macros:
                self.error("A macro cannot have the same name as an existing command")
                return -1

            rc = self.record_macro(shell, ns.name)
        else:
            self.usage_error(shell, "missing required argument: NAME")
            rc = 1

        return rc

    def end_block(self, shell: Shell, lines: List[str]) -> None:
        self.add_macro(shell, shell.ctx.recording_macro_name, lines)
        shell.ctx.recording_macro_name = None
        shell.eof_is_sigint = shell.ctx.macro_orig_eof_is_sigint

    def cancel_block(self, shell: Shell):
        shell.ctx.recording_macro_name = None
        shell.eof_is_sigint = shell.ctx.macro_orig_eof_is_sigint

    def add_macro(self, shell: Shell, name: str, lines: List[str]):
        shell.register(Macro(lines=lines, name=name, topic='__hidden__'))
        shell.ctx.macros[name] = lines

    def print_macro(self, shell: Shell, name: str) -> int:
        macro = shell.ctx.macros.get(name)  # TODO case sensitive?
        if macro is not None:
            print(f"macro {name}")
            for line in macro:
                print(f"    {line}")
            print("end")
            rc = 0
        else:
            self.error(f"unknown macro: {name}")
            rc = -1

        return rc

    def delete_macro(self, shell: Shell, name: str) -> int:
        if name in shell.ctx.macros:  # TODO case sensitive?
            del shell.ctx.macros[name]
            # It gets registered as a command too. See line 230 in this
            # file and register() in shell.py
            del shell.commands[name]
            rc = 0
        else:
            self.error(f"unknown macro: {name}")
            rc = -1

        return rc

    def print_macro_list(self, shell: Shell) -> int:
        print(ansi_title("Registered Macros"))
        chunk_size = 3

        tbl = Table(
            columns=3,
            spacing=4,
            header=False,
            width=sys.stdout.width
        )

        macro_names = list(shell.ctx.macros.keys())
        for i in range(0, len(macro_names), chunk_size):
            chunk = macro_names[i:i + chunk_size]
            tbl.extend(chunk)
        tbl.write(sys.stdout)

        return 0

    def record_macro(self, shell: Shell, name: str) -> int:
        shell.ctx.recording_macro_name = name
        self.begin_block(shell)
        if sys.stdin.isatty():
            print(f"Beginning macro, use the '{shell.ctx.block.end_cmd}' command to save.")

        shell.ctx.macro_orig_eof_is_sigint = shell.eof_is_sigint
        shell.eof_is_sigint = True

        return 0
