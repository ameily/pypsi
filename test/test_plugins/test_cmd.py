from pypsi.plugins.cmd import CmdPlugin
from pypsi.shell import Shell


class PluginShell(Shell):
    plugin = CmdPlugin()


class TestCmdPlugin:

    def setup(self):
        self.shell = PluginShell()

    def teardown(self):
        self.shell.restore()
