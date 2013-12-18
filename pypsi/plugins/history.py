
from pypsi.base import Command, Plugin, PypsiArgParser
import argparse

CmdUsage = """%(prog)s SUBCMD
   or: %(prog)s -l [N]
   or: %(prog)s -c
   or: %(prog)s -d N
   or: %(prog)s -o PATH
   or: %(prog)s -i PATH"""

class HistoryCommand(Command):

    def __init__(self, name='history', **kwargs):
        self.setup_parser()
        super(HistoryCommand, self).__init__(name=name, usage=self.parser.format_help(), **kwargs)

    def setup_parser(self):
        self.parser = PypsiArgParser(
            prog='history',
            description="Manage shell history",
            usage=CmdUsage
        )

        subcmd = self.parser.add_mutually_exclusive_group(required=False)
        subcmd.add_argument(
            '-c', '--clear',
            help='clear the history',
            action='store_true'
        )

        subcmd.add_argument(
            '-l', '--list',
            help='list N most recent history items',
            action='store',
            type=int,
            const=0,
            nargs='?',
            metavar='N'
        )

        subcmd.add_argument(
            '-d', '--delete',
            help='delete item at N',
            action='store',
            type=int,
            metavar='N'
        )

        subcmd.add_argument(
            '-o', '--out',
            help='save history',
            action='store',
            metavar='PATH'
        )

        subcmd.add_argument(
            '-i', '--in',
            help='load history',
            action='store',
            metavar='PATH'
        )

    def run(self, shell, args, ctx):
        ns = self.parser.parse_args(args)
        if self.parser.last_error:
            print self.parser.last_error
            return 1

        return 0




class HistoryPlugin(Plugin):

    def __init__(self, history_cmd='history', **kwargs):
        super(HistoryPlugin, self).__init__(**kwargs)
        self.history_cmd = HistoryCommand(name=history_cmd)

    def setup(self, shell):
        #shell.features.history = History()
        shell.register(self.history_cmd)
