from pypsi.plugins.comment import CommentPlugin
from pypsi.shell import Shell


class PluginShell(Shell):
    plugin = CommentPlugin()


class TestCommentPlugin:

    def setup(self):
        self.shell = PluginShell()

    def teardown(self):
        self.shell.restore()
