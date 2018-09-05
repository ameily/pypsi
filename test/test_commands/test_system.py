from pypsi.shell import Shell
from pypsi.commands.system import SystemCommand

class CmdShell(Shell):
    system = SystemCommand()


class TestSystem:

    def setup(self):
        self.shell = CmdShell()

    def teardown(self):
        self.shell.restore()
