
from pypsi.base import Command, PypsiArgParser
import sys
import argparse

XArgsUsage = """{name} [-h] [-I repstr] command"""


class XArgsCommand(Command):
    '''
    Execute a command for each line of input from :data:`sys.stdin`.
    '''

    def __init__(self, name='xargs', topic='shell', **kwargs):
        self.parser = PypsiArgParser(
            prog=name,
            description='build and execute command lines from stdin',
            usage=XArgsUsage.format(name=name)
        )

        self.parser.add_argument(
            '-I', default='{}', action='store',
            metavar='repstr', help='string token to replace',
            dest='token'
        )

        self.parser.add_argument(
            'command', nargs=argparse.REMAINDER, help="command to execute"
        )

        super(XArgsCommand, self).__init__(
            name=name, topic=topic, usage=self.parser.format_help(),
            brief='build and execute command lines from stdin', **kwargs
        )

    def run(self, shell, args, ctx):
        ns = self.parser.parse_args(args)
        if self.parser.rc is not None:
            return self.parser.rc

        if not ns.command:
            self.error(shell, "missing command")
            return 1

        base = ' '.join([
            '"{}"'.format(c.replace('"', '\\"')) for c in ns.command
        ])

        child = ctx.fork()
        for line in sys.stdin:
            cmd = base.replace(ns.token, line.strip())
            shell.execute(cmd, child)

        return 0
