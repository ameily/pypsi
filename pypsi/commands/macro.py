
from pypsi.plugins.block import BlockCommand
from pypsi.base import Command


# something | macro | something
# =>
# something | cmd1 ; cmd2 | something

class Macro(Command):

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