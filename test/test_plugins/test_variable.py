from pypsi.plugins.variable import VariablePlugin, VariableCommand
from pypsi.shell import Shell


class PluginShell(Shell):
    plugin = VariablePlugin()


class TestVariablePlugin:

    def setup(self):
        self.shell = PluginShell()

    def teardown(self):
        self.shell.restore()
