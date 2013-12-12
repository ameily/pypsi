
from pypsi.plugins.block import BlockCommand

class MacroCommand(BlockCommand):

    def __init__(self, name='macro', **kwargs):
        super(MacroCommand, self).__init__(name=name, **kwargs)

    def run(self, shell, args, ctx):
        self.macro_name = args[0]
        self.begin_block(shell)

    def end_block(self, shell, lines):
        print "Macro DONE!"
        for line in lines:
            print ">>>>",line
        return 0
