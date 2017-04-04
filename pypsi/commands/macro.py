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

from pypsi.plugins.block import BlockCommand
from pypsi.core import Command, PypsiArgParser, CommandShortCircuit
from pypsi.format import Table, Column, title_str
from pypsi.completers import command_completer
import sys


# something | macro | something
# =>
# something | cmd1 ; cmd2 | something

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

    def __init__(self, lines, **kwargs):
        super(Macro, self).__init__(**kwargs)
        self.lines = lines

    def run(self, shell, args):
        rc = None
        self.add_var_args(shell, args)

        for line in self.lines:
            rc = shell.execute(line)

        self.remove_var_args(shell)
        return rc

    def add_var_args(self, shell, args):
        if 'vars' in shell.ctx:
            shell.ctx.vars['0'] = self.name
            for i in range(0, 9):
                if i < len(args):
                    shell.ctx.vars[str(i+1)] = args[i]
                else:
                    shell.ctx.vars[str(i+1)] = ''

    def remove_var_args(self, shell):
        if 'vars' in shell.ctx:
            for i in range(0, 10):
                s = str(i)
                if s in shell.ctx.vars:
                    del shell.ctx.vars[s]


MacroCmdUsage = """%(prog)s -l
   or: %(prog)s NAME
   or: %(prog)s [-d] [-s] NAME"""


class MacroCommand(BlockCommand):
    '''
    Record and execute command macros. Macros can consist of one or more
    command statements. Macros are comparable to Bash functions. Once a macro
    has been recorded, a new command is registered in the shell as an instance
    of a :class:`Macro`.

    This command requires the :class:`pypsi.plugins.block.BlockPlugin` plugin.
    '''

    def __init__(self, name='macro', topic='shell',
                 brief="manage registered macros", macros=None, **kwargs):
        self.parser = PypsiArgParser(
            prog=name,
            description=brief,
            usage=MacroCmdUsage
        )

        self.parser.add_argument(
            '-l', '--list', help='list all macros', action='store_true'
        )
        self.parser.add_argument(
            '-d', '--delete', help='delete macro',
            metavar='NAME', completer=self.complete_macros
        )
        self.parser.add_argument(
            '-s', '--show', help='print macro body',
            metavar='NAME', completer=self.complete_macros
        )
        self.parser.add_argument(
            'name', help='macro name', nargs='?', metavar='NAME'
        )

        super(MacroCommand, self).__init__(
            name=name, usage=self.parser.format_help(), brief=brief,
            topic=topic, **kwargs
        )
        self.base_macros = macros or {}

    def complete_macros(self, shell, args, prefix):
        # returns a list of macro names in the current shell
        return list(shell.ctx.macros.keys())

    def complete(self, shell, args, prefix):
        # The command_completer function takes in the parser, automatically
        # completes optional arguments (ex, '-v'/'--verbose') or sub-commands,
        # and complete any arguments' values by calling a callback function
        # with the same arguments as complete if the callback was defined
        # when the parser was created.
        return command_completer(self.parser, shell, args, prefix)

    def setup(self, shell):
        rc = 0

        if 'macros' not in shell.ctx:
            shell.ctx.macros = {}

        for name in self.base_macros:
            rc = self.add_macro(shell, name, shell.ctx.macros[name])

        return rc

    def run(self, shell, args):
        try:
            ns = self.parser.parse_args(args)
        except CommandShortCircuit as e:
            return e.code

        rc = 0
        if ns.show:
            if ns.delete or ns.name:
                self.usage_error(shell,
                                 'incompatible arguments: -s/--show and ',
                                 '-d/--delete' if ns.delete else 'NAME')
                return -1
            if ns.list or ns.name:
                self.usage_error(shell,
                                 'incompatible arguments: -s/--show and ',
                                 '-l/--list' if ns.list else 'NAME')
                return -1

            if ns.show in shell.ctx.macros:
                print("macro ", ns.show, sep='')
                for line in shell.ctx.macros[ns.show]:
                    print("    ", line, sep='')
                print("end")
            else:
                self.error(shell, "unknown macro ", ns.show)
                rc = -1
        elif ns.delete:
            if ns.list or ns.name:
                self.usage_error(shell,
                                 'incompatible arguments: -d/--delete and ',
                                 '-l/--list' if ns.list else 'NAME')
                return -1

            if ns.delete in shell.ctx.macros:
                del shell.ctx.macros[ns.delete]
                # It gets registered as a command too. See line 230 in this
                # file and register() in shell.py
                del shell.commands[ns.delete]
            else:
                self.error(shell, "unknown macro ", ns.delete)
                rc = -1
        elif ns.name:
            if ns.list:
                self.usage_error(shell,
                                 "list option does not take an argument")
            else:
                if (ns.name in shell.commands.keys() and
                        ns.name not in shell.ctx.macros):
                    self.error(
                        shell, "A macro cannot have the same name as an ",
                        "existing command."
                    )
                    return -1

                self.macro_name = ns.name
                self.begin_block(shell)
                if sys.stdin.isatty():
                    print("Beginning macro, use the '",
                          shell.ctx.block.end_cmd, "' command to save.",
                          sep='')

                shell.ctx.macro_orig_eof_is_sigint = shell.eof_is_sigint
                shell.eof_is_sigint = True
        elif ns.list:
            '''
            Left justified table
            '''
            print(title_str("Registered Macros", shell.width))
            chunk_size = 3

            tbl = Table(
                columns=(Column(''), Column(''), Column('', Column.Grow)),
                spacing=4,
                header=False,
                width=shell.width
            )

            macro_names = list(shell.ctx.macros.keys())
            for i in range(0, len(macro_names), chunk_size):
                chunk = macro_names[i:i+chunk_size]
                tbl.extend(chunk)
            tbl.write(sys.stdout)
        else:
            self.usage_error(shell, "missing required argument: NAME")
            rc = 1

        return rc

    def end_block(self, shell, lines):
        self.add_macro(shell, self.macro_name, lines)
        self.macro_name = None
        shell.eof_is_sigint = shell.ctx.macro_orig_eof_is_sigint
        return 0

    def cancel_block(self, shell):
        self.macro_name = None
        shell.eof_is_sigint = shell.ctx.macro_orig_eof_is_sigint

    def add_macro(self, shell, name, lines):
        shell.register(
            Macro(lines=lines, name=name, topic='__hidden__')
        )
        shell.ctx.macros[name] = lines
        return 0
