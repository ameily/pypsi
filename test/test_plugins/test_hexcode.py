from pypsi.plugins.hexcode import HexCodePlugin
from pypsi.shell import Shell


class PluginShell(Shell):
    plugin = HexCodePlugin()


class TestHexCodePlugin:

    def setup(self):
        self.shell = PluginShell()

    def teardown(self):
        self.shell.restore()
