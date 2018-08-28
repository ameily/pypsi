from pypsi.shell import Shell
from pypsi.commands.include import IncludeCommand

class CmdShell(Shell):
    include = IncludeCommand()


class TestInclude:

    def setup(self):
        self.shell = CmdShell()

    def teardown(self):
        self.shell.restore()
