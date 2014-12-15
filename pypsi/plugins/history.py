#
# Copyright (c) 2014, Adam Meily
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without modification,
# are permitted provided that the following conditions are met:
#
# * Redistributions of source code must retain the above copyright notice, this
#   list of conditions and the following disclaimer.
#
# * Redistributions in binary form must reproduce the above copyright notice, this
#   list of conditions and the following disclaimer in the documentation and/or
#   other materials provided with the distribution.
#
# * Neither the name of the {organization} nor the names of its
#   contributors may be used to endorse or promote products derived from
#   this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR
# ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON
# ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#

from pypsi.base import Command, Plugin, PypsiArgParser, CommandShortCircuit
from pypsi.utils import safe_open
from pypsi.completers import path_completer
import argparse
import readline
import os

CmdUsage = """%(prog)s clear
   or: %(prog)s delete N
   or: %(prog)s list [N]
   or: %(prog)s load PATH
   or: %(prog)s save PATH"""


class HistoryCommand(Command):
    '''
    Interact with and manage the shell's history.
    '''

    def __init__(self, name='history', brief='manage shell history', topic='shell', **kwargs):
        self.setup_parser(brief)
        super(HistoryCommand, self).__init__(
            name=name, usage=self.parser.format_help(), topic=topic,
            brief=brief, **kwargs
        )

    def complete(self, shell, args, prefix):
        if len(args) == 1:
            return [x for x in ('clear', 'delete', 'list', 'load', 'save') if x.startswith(prefix)]

        if len(args) == 2:
            if args[0] == 'save' or args[0] == 'load':
                return path_completer(shell, args, prefix)
        return []

    def setup_parser(self, brief):
        self.parser = PypsiArgParser(
            prog='history',
            description=brief,
            usage=CmdUsage
        )

        subcmd = self.parser.add_subparsers(prog='history', dest='subcmd', metavar='subcmd')
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


    def run(self, shell, args, ctx):
        try:
            ns = self.parser.parse_args(args) #(shell, args)
        except CommandShortCircuit as e:
            return e.code

        rc = 0
        if ns.subcmd == 'list':
            start = 0
            if ns.count:
                start = len(shell.ctx.history) - ns.count
                if start < 0:
                    start = 0

            i = start + 1
            for event in shell.ctx.history[start:]:
                print(i, '    ', event, sep='')
                i += 1
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
    '''
    Provides access to the shell's statement history.
    '''

    def __init__(self, history_cmd='history', **kwargs):
        super(HistoryPlugin, self).__init__(**kwargs)
        self.history_cmd = HistoryCommand(name=history_cmd)

    def setup(self, shell):
        '''
        Adds a reference to the current :class:`History` in the shell's context.
        The history can be accessed by retrieving the ``shell.ctx.history``
        attribute.
        '''
        shell.register(self.history_cmd)
        if 'history' not in shell.ctx:
            shell.ctx.history = History()


class History(object):
    '''
    Wraps the :mod:`readline` module. Provides the following abilities:

    - Accessing and manipulating history items via :meth:`__getitem__`, 
      :meth:`__setitem__`, :meth:`__delitem__`, and :meth:`__iter__`. Indexes
      must be :class:`int` and negative indexes are handled and automatically
      normalized before passing them to :mod:`readline`. :meth:`__getitem__` 
      also supports slicing, which also normalizes negative indexes.
    - Appending new history items via :meth:`append`.
    - Clearing all history items via :meth:`clear`.

    Methods that access an index (or slice) will raise an
    :class:`IndexError` if the index is invalid or out of range of the history.
    '''

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
        '''
        Get a single event at ``index`` or a :class:`slice` of events.
        '''
        if isinstance(index, slice):
            if not self.__len__():
                return []
            start = self.normalize_index(index.start or 0)
            stop = self.normalize_index((index.stop or self.__len__())-1)
            step = index.step or 1
            return [readline.get_history_item(i) for i in range(start, stop+1, step)]
        else:
            index = self.normalize_index(index)
            return readline.get_history_item(index)

    def __len__(self):
        '''
        Get the number of history events.
        '''
        return readline.get_current_history_length()

    def __setitem__(self, index, value):
        '''
        Set the history event at ``index``.
        '''
        index = self.normalize_index(index)
        readline.replace_history_item(index, value)

    def __delitem__(self, index):
        '''
        Delete a history event at ``index``.
        '''
        index = self.normalize_index(index)
        readline.remove_history_item(index)

    def __nonzero__(self):
        return len(self) > 0

    def __iter__(self):
        return iter(self.__getitem__(slice(None, None, None)))

    def append(self, event):
        '''
        Append a new history event.

        :param str event: event to append
        '''
        readline.add_history(event)

    def search_prefix(self, prefix):
        '''
        Find the most recent event that starts with the provided prefix.
        Provides a Bash ``![prefix]``-esque interface.

        :param str prefix: the prefix to search for
        :returns str: the event, if found, :const:`None` if no matching event is
            found
        '''
        for i in range(self.__len__(), 0, -1):
            event = readline.get_history_item(i)
            if event.startswith(prefix):
                return event
        return None

    def clear(self):
        '''
        Remove all history events.
        '''
        readline.clear_history()
