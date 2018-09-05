from pypsi.plugins.multiline import MultilinePlugin
from pypsi.shell import Shell


class PluginShell(Shell):
    plugin = MultilinePlugin()


class TestMultilinePlugin:

    def setup(self):
        self.shell = PluginShell()

    def teardown(self):
        self.shell.restore()
