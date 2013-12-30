
from pypsi.base import Command, Plugin, PypsiArgParser
from pypsi.utils import safe_open
import argparse
import readline
import os

CmdUsage = """%(prog)s list [N]
   or: %(prog)s clear
   or: %(prog)s delete N
   or: %(prog)s save PATH
   or: %(prog)s load PATH
   or: %(prog)s exec PREFIX"""

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

        subcmd = self.parser.add_subparsers(prog='history', dest='subcmd')
        subcmd.required = True

        ls = subcmd.add_parser('list', help='list history events')
        ls.add_argument(
            'count', metavar='N', type=int, help='number of events to display', nargs='?'
        )

        subcmd.add_parser('clear', help='remove all history events')
        delete = subcmd.add_parser('delete', help='delete single history event')
        delete.add_argument(
            'index', metavar='N', type=int, help='remove item at index N',
        )

        save = subcmd.add_parser('save', help='save history to a file')
        save.add_argument(
            'path', metavar='PATH', help='save history to file located at PATH'
        )

        load = subcmd.add_parser('load', help='load history from a file')
        load.add_argument(
            'path', metavar='PATH', help='load history from file located at PATH'
        )

        exe = subcmd.add_parser('exec', help='execute previous history event')
        exe.add_argument(
            'prefix', metavar='PREFIX', help='find and execute previous history event with give PREFIX'
        )

    def run(self, shell, args, ctx):
        ns = self.parser.parse_args(shell, args)
        if self.parser.rc is not None:
            return self.parser.rc

        rc = 0
        if ns.subcmd == 'list':
            start = 0
            if ns.count:
                start = len(shell.ctx.history) - ns.count
                if start < 0:
                    start = 0

            i = start + 1
            for event in shell.ctx.history[start:]:
                shell.info(i, '    ', event, '\n')
                i += 1
        elif ns.subcmd == 'exec':
            event = None
            if ns.prefix.isdigit() or (ns.prefix[0] == '-' and ns.prefix[1:].isdigit()):
                try:
                    index = int(ns.prefix) - 1
                    event = shell.ctx.history[index]
                except ValueError:
                    self.error(shell, "invalid event index\n")
                    rc = -1
                except IndexError as e:
                    self.error(shell, "invalid event index\n")
                    rc = -1
            else:
                event = shell.ctx.history.search_prefix(ns.prefix)
                if event is None:
                    shell.error("event not found\n")
                    rc = -1

            if event:
                shell.info("found event: ", event, '\n')
        elif ns.subcmd == 'clear':
            shell.ctx.history.clear()
        elif ns.subcmd == 'delete':
            try:
                del shell.ctx.history[ns.index - 1]
            except:
                self.error(shell, "invalid event index\n")
                rc = -1
        elif ns.subcmd == 'save':
            try:
                with open(ns.path, 'w') as fp:
                    for event in shell.ctx.history:
                        fp.write(event)
                        fp.write('\n')
            except IOError as e:
                self.error(shell, "error saving history to file: ",
                           os.strerror(e.errno), '\n')
                rc = -1
        elif ns.subcmd == 'load':
            try:
                lines = []
                with safe_open(ns.path, 'r') as fp:
                    for event in fp:
                        lines.append(str(event))

                shell.ctx.history.clear()
                for line in lines:
                    shell.ctx.history.append(line.strip())
            except IOError as e:
                self.error(shell, "error saving history to file: ",
                           os.strerror(e.errno), '\n')
                rc = -1
            except UnicodeEncodeError:
                self.error(shell, "error: file contains invalide unicode characters\n")

        return rc


class HistoryPlugin(Plugin):

    def __init__(self, history_cmd='history', **kwargs):
        super(HistoryPlugin, self).__init__(**kwargs)
        self.history_cmd = HistoryCommand(name=history_cmd)

    def setup(self, shell):
        shell.register(self.history_cmd)
        if 'history' not in shell.ctx:
            shell.ctx.history = History()


class History(object):

    def __init__(self):
        pass

    def normalize_index(self, index):
        count = self.__len__()
        if index < 0:
            index = count + index

        if index < 0 or index >= count:
            raise IndexError(str(index))
        return index+1

    def __getitem__(self, index):
        if isinstance(index, slice):
            start = self.normalize_index(index.start or 0)
            stop = self.normalize_index((index.stop or self.__len__())-1)
            step = index.step or 1
            return [readline.get_history_item(i) for i in range(start, stop+1, step)]
        else:
            index = self.normalize_index(index)
            return readline.get_history_item(index)

    def __len__(self):
        return readline.get_current_history_length()

    def __setitem__(self, index, value):
        index = self.normalize_index(index)
        readline.replace_history_item(index, value)

    def __delitem__(self, index):
        index = self.normalize_index(index)
        readline.remove_history_item(index)

    def __iter__(self):
        return iter(self.__getitem__(slice(None, None, None)))

    def append(self, event):
        readline.add_history(event)

    def search_prefix(self, prefix):
        for i in range(self.__len__(), 0, -1):
            event = readline.get_history_item(i)
            if event.startswith(prefix):
                return event
        return None

    def clear(self):
        readline.clear_history()
