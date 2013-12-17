
from pypsi.shell import Shell
from pypsi.base import Command
#from pypsi.plugins.alias import AliasPlugin
from pypsi.plugins.block import BlockPlugin
from pypsi.plugins.hexcode import HexCodePlugin
from pypsi.commands.macro import MacroCommand
from pypsi.commands.system import SystemCommand
from pypsi.plugins.multiline import MultilinePlugin
from pypsi.commands.xargs import XArgsCommand
from pypsi.commands.exit import ExitCommand
import sys

class TestCommand(Command):

    def __init__(self, name='test', **kwargs):
        super(TestCommand, self).__init__(name=name, **kwargs)

    def run(self, shell, args, ctx):
        print "TEST!"
        return 0


class PrintCommand(Command):

    def __init__(self, name='print', **kwargs):
        super(PrintCommand, self).__init__(name=name, **kwargs)

    def run(self, shell, args, ctx):
        if args and args[0] == '-i':
            for line in sys.stdin:
                print "line:",line.strip()
        else:
            print ' '.join(args)

        return 0


class DevShell(Shell):

    test_cmd = TestCommand()
    print_cmd = PrintCommand()
    block_plugin = BlockPlugin()
    hexcode_plugin = HexCodePlugin()
    macro_cmd = MacroCommand()
    system_cmd = SystemCommand()
    ml_plugin = MultilinePlugin()
    xargs_cmd = XArgsCommand()
    exit_cmd = ExitCommand()

    def __init__(self):
        super(DevShell, self).__init__()


if __name__ == '__main__':
    shell = DevShell()
    shell.cmdloop()
