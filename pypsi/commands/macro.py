
from pypsi.plugins.block import BlockCommand
from pypsi.base import Command

class Macro(Command):

    def __init__(self, lines, **kwargs):
        super(Macro, self).__init__(**kwargs)
        self.lines = lines

    def run(self, shell, args, ctx):
        rc = None
        for line in self.lines:
            rc = shell.execute(line)
        return rc


class MacroCommand(BlockCommand):

    def __init__(self, name='macro', **kwargs):
        super(MacroCommand, self).__init__(name=name, **kwargs)

    def run(self, shell, args, ctx):
        self.macro_name = args[0]
        self.begin_block(shell)

    def end_block(self, shell, lines):
        shell.register(
            Macro(lines=lines, name=self.macro_name)
        )
        self.macro_name = None
        return 0
