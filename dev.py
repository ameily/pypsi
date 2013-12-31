
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
from pypsi.plugins.variable import VariablePlugin
from pypsi.plugins.history import HistoryPlugin
from pypsi.commands.echo import EchoCommand
from pypsi.commands.include import IncludeCommand
from pypsi.commands.help import HelpCommand
import sys


class TestCommand(Command):

    def __init__(self, name='test', **kwargs):
        super(TestCommand, self).__init__(name=name, **kwargs)

    def run(self, shell, args, ctx):
        print("TEST!")
        return 0


class DevShell(Shell):

    test_cmd = TestCommand()
    echo_cmd = EchoCommand()
    block_plugin = BlockPlugin()
    hexcode_plugin = HexCodePlugin()
    macro_cmd = MacroCommand()
    system_cmd = SystemCommand()
    ml_plugin = MultilinePlugin()
    xargs_cmd = XArgsCommand()
    exit_cmd = ExitCommand()
    history_plugin = HistoryPlugin()
    include_cmd = IncludeCommand()
    help_cmd = HelpCommand(
        topics=(('shell', "Shell"), ('misc', 'Miscellaneous'))
    )
    var_plugin = VariablePlugin(case_sensitive=False)

    def __init__(self):
        super(DevShell, self).__init__()
        self.prompt = "\\x1b[1;32mpypsi @ $date-$time )>\\x1b[0m "
        self.error.prefix = "\x1b[1;31m"
        self.warn.postfix = self.error.postfix = "\x1b[0m"
        self.warn.prefix = "\x1b[1;33m"
        self.fallback_cmd = self.system_cmd

if __name__ == '__main__':
    shell = DevShell()
    shell.cmdloop()
