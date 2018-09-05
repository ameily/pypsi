from pypsi.plugins.block import BlockCommand, BlockPlugin
from pypsi.shell import Shell


class PluginShell(Shell):
    plugin = BlockPlugin()


class TestBlockPlugin:

    def setup(self):
        self.shell = PluginShell()

    def teardown(self):
        self.shell.restore()
