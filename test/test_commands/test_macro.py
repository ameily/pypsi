from pypsi.shell import Shell
from pypsi.commands.macro import MacroCommand

class CmdShell(Shell):
    macro = MacroCommand()


class TestMacro:

    def setup(self):
        self.shell = CmdShell()

    def teardown(self):
        self.shell.restore()
