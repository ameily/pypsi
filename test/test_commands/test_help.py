from pypsi.shell import Shell
from pypsi.commands.help import HelpCommand

class CmdShell(Shell):
    help_cmd = HelpCommand()


class TestHelp:

    def setup(self):
        self.shell = CmdShell()

    def teardown(self):
        self.shell.restore()
