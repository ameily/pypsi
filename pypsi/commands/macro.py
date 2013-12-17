
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
        next = ctx.fork()
        for line in self.lines:
            rc = shell.execute(line, next)
        #ctx.stdout = next.stdout
        return rc


MacroCmdUsage = """usage: {name} -l
   or: {name} NAME
   or: {name} -[dr] NAME
Manage registered macros"""


class MacroCommand(BlockCommand):

    def __init__(self, name='macro', macros={}, usage=MacroCmdUsage, **kwargs):
        super(MacroCommand, self).__init__(name=name, usage=usage, **kwargs)
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
                    print name
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