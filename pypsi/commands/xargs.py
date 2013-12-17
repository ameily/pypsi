
from pypsi.base import Command
import sys

XArgsUsage = """
"""

class XArgsCommand(Command):

    def __init__(self, name='xargs', **kwargs):
        super(XArgsCommand, self).__init__(name=name, **kwargs)

    def run(self, shell, args, ctx):
        argc = len(args)
        if not argc:
            return 1

        base = ' '.join([
            '"{}"'.format(c.replace('"', '\\"')) for c in args
        ])

        child = ctx.fork()
        for line in sys.stdin:
            cmd = base.replace('{}', line.strip())
            shell.execute(cmd, child)
        return 0
