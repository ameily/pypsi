import os
import pytest
from pypsi.shell import Shell
from pypsi.commands.chdir import ChdirCommand

class CmdShell(Shell):
    chdir = ChdirCommand()


class TestChdir:

    def setup(self):
        self.shell = CmdShell()

    def teardown(self):
        self.shell.restore()

    def test_setup(self):
        assert self.shell.ctx.chdir_last_dir == os.getcwd()
