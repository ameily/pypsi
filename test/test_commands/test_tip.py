from pypsi.shell import Shell
from pypsi.commands.tip import TipCommand

class CmdShell(Shell):
    tip = TipCommand()


class TestTip:

    def setup(self):
        self.shell = CmdShell()

    def teardown(self):
        self.shell.restore()
