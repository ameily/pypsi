from pypsi.shell import Shell
from pypsi.commands.echo import EchoCommand

class CmdShell(Shell):
    echo = EchoCommand()


class TestEcho:

    def setup(self):
        self.shell = CmdShell()

    def teardown(self):
        self.shell.restore()
