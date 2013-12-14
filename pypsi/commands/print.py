
from pypsi.base import Command

class PrintCommand(Command):

    def __init__(self, name='print', **kwargs):
        super(PrintCommand, self).__init__(name=name, **kwargs)

    def run(self, shell, args, ctx):
        print ' '.join(args)
        return 0
