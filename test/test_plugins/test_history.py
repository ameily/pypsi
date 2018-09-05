from pypsi.plugins.history import HistoryCommand, HistoryPlugin
from pypsi.shell import Shell


class PluginShell(Shell):
    plugin = HistoryPlugin()


class TestHistoryPlugin:

    def setup(self):
        self.shell = PluginShell()

    def teardown(self):
        self.shell.restore()
