from pypsi.shell import Shell
from pypsi.commands.exit import ExitCommand

class CmdShell(Shell):
    exit_cmd = ExitCommand()


class TestExit:

    def setup(self):
        self.shell = CmdShell()

    def teardown(self):
        self.shell.restore()
