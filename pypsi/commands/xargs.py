
from pypsi.base import Command, PypsiArgParser
import sys
import argparse

XArgsUsage = "%(prog)s [-h] [-I repstr] command"

class XArgsCommand(Command):

    def __init__(self, name='xargs', **kwargs):
        self.parser = PypsiArgParser(
            prog=name,
            description='build and execute command lines from stdin',
            usage=XArgsUsage
        )

        self.parser.add_argument(
            '-I', default='{}', action='store',
            metavar='repstr', help='string token to replace',
            dest='token'
        )

        self.parser.add_argument(
            'command', nargs=argparse.REMAINDER, help="command to execute"
        )

        super(XArgsCommand, self).__init__(name=name, usage=self.parser.format_help(), **kwargs)

    def run(self, shell, args, ctx):
        ns = self.parser.parse_args(args)
        if self.parser.last_error:
            self.error(shell, self.parser.last_error)
            return 1

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
