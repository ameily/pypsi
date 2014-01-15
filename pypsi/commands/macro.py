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

from pypsi.plugins.block import BlockCommand
from pypsi.base import Command


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

    def run(self, shell, args, ctx):
        rc = None
        self.add_var_args(shell, args)

        next = ctx.fork()
        for line in self.lines:
            rc = shell.execute(line, next)

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


MacroCmdUsage = """usage: {name} -l
   or: {name} NAME
   or: {name} -[dr] NAME
Manage registered macros"""


class MacroCommand(BlockCommand):
    '''
    Record and execute command macros. Macros can consist of one or more
    command statements. Macros are comparable to Bash functions. Once a macro
    has been recorded, a new command is registered in the shell as an instance
    of a :class:`Macro`.
    
    This command requires the :class:`pypsi.plugins.block.BlockPlugin` plugin.
    '''

    def __init__(self, name='macro', topic='shell', macros={}, **kwargs):
        super(MacroCommand, self).__init__(name=name, usage=MacroCmdUsage, brief='manage registered macros', topic=topic, **kwargs)
        self.macros = macros or {}

    def setup(self, shell):
        for name in self.macros:
            self.add_macro(shell, name, self.macros[name])
        return 0

    def run(self, shell, args, ctx):
        argc = len(args)
        rc = 0
        if argc == 0:
            rc = 1
        elif argc == 1:
            rc = 0
            if args[0] == '-l':
                for name in self.macros:
                    shell.info(name, '\n')
            else:
                self.macro_name = args[0]
                self.begin_block(shell)
        return rc

    def end_block(self, shell, lines):
        self.add_macro(shell, self.macro_name, lines)
        self.macro_name = None
        return 0

    def add_macro(self, shell, name, lines):
        shell.register(
            Macro(lines=lines, name=name)
        )
        self.macros[name] = lines
        return 0