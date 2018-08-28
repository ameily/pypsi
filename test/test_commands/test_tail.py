from pypsi.shell import Shell
from pypsi.commands.tail import TailCommand

class CmdShell(Shell):
    tail = TailCommand()


class TestTail:

    def setup(self):
        self.shell = CmdShell()

    def teardown(self):
        self.shell.restore()
