from pypsi.shell import Shell
from pypsi.commands.xargs import XArgsCommand

class CmdShell(Shell):
    xargs = XArgsCommand()


class TestXArgs:

    def setup(self):
        self.shell = CmdShell()

    def teardown(self):
        self.shell.restore()
