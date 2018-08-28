from pypsi.shell import Shell
from pypsi.commands.pwd import PwdCommand


class CmdShell(Shell):
    pwd = PwdCommand()


class TestPwd:

    def setup(self):
        self.shell = CmdShell()

    def teardown(self):
        self.shell.restore()
