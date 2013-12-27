
from pypsi.base import Command

class ExitCommand(Command):

    Usage = """usage: {name}
Exit the {shell} shell"""

    def __init__(self, name='exit', topic='shell', **kwargs):
        super(ExitCommand, self).__init__(name=name, usage=self.Usage, topic=topic, brief="exit the shell", **kwargs)

    def run(self, shell, args, ctx):
        return shell.exit_rc
