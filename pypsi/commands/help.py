#
# Copyright (c) 2015, Adam Meily <meily.adam@gmail.com>
# Pypsi - https://github.com/ameily/pypsi
#
# Permission to use, copy, modify, and/or distribute this software for any
# purpose with or without fee is hereby granted, provided that the above
# copyright notice and this permission notice appear in all copies.
#
# THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
# WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
# MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
# ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
# WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
# ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
# OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
#

from pypsi.core import Command, PypsiArgParser, CommandShortCircuit
from pypsi.format import Table, Column, title_str
from pypsi.ansi import AnsiCodes
from pypsi.completers import command_completer
import sys


class Topic(object):

    def __init__(self, id, name=None, content=None, commands=None):
        self.id = id
        self.name = name or ''
        self.content = content or ''
        self.commands = commands or []


class HelpCommand(Command):
    '''
    Provides access to manpage-esque topics and command usage information.
    '''

    def __init__(self, name='help', topic='shell',
                 brief='print information on a topic or command', topics=None,
                 vars=None, **kwargs):
        self.parser = PypsiArgParser(
            prog=name,
            description=brief
        )

        # Add a callback to self.complete_topics so tab-complete can
        # return the possible topics you may get help on
        self.parser.add_argument(
            "topic", metavar="TOPIC", help="command or topic to print",
            nargs='?', completer=self.complete_topics
        )

        super(HelpCommand, self).__init__(
            name=name, brief=brief, usage=self.parser.format_help(),
            topic=topic, **kwargs
        )

        self.vars = vars or {}
        self.topics = topics

    def setup(self, shell):
        shell.ctx.topics = list(self.topics or [])
        shell.ctx.uncat_topic = Topic('uncat',
                                      'Uncategorized Commands & Topics')
        shell.ctx.topic_lookup = {t.id: t for t in shell.ctx.topics}
        shell.ctx.topics_dirty = True

    def complete_topics(self, shell, args, prefix):
        completions = [
            x.id for x in shell.ctx.topics
            if x.id.startswith(prefix) or not prefix
            ]

        completions.extend([
            x for x in shell.commands if x.startswith(prefix) or not prefix
        ])
        return sorted(completions)

    def complete(self, shell, args, prefix):
        if shell.ctx.topics_dirty:
            self.reload(shell)

        # The command_completer function takes in the parser, automatically
        # completes optional arguments (ex, '-v'/'--verbose') or sub-commands,
        # and complete any arguments' values by calling a callback function
        # with the same arguments as complete if the callback was defined
        # when the parser was created.
        return command_completer(self.parser, shell, args, prefix)

    def reload(self, shell):
        shell.ctx.uncat_topic.commands = []
        for id in shell.ctx.topic_lookup:
            shell.ctx.topic_lookup[id].commands = []

        for (name, cmd) in shell.commands.items():
            if cmd.topic == '__hidden__':
                continue

            if cmd.topic:
                if cmd.topic in shell.ctx.topic_lookup:
                    shell.ctx.topic_lookup[cmd.topic].commands.append(cmd)
                else:
                    self.add_topic(shell, Topic(cmd.topic, commands=[cmd]))
            else:
                shell.ctx.uncat_topic.commands.append(cmd)
        shell.ctx.topics_dirty = False

        for topic in shell.ctx.topics:
            if topic.commands:
                topic.commands = sorted(topic.commands, key=lambda x: x.name)

    def add_topic(self, shell, topic):
        shell.ctx.topics_dirty = True
        shell.ctx.topic_lookup[topic.id] = topic
        shell.ctx.topics.append(topic)

    def print_topic_commands(self, shell, topic, title=None,
                             name_col_width=20):
        print(
            AnsiCodes.yellow,
            title_str(title or topic.name or topic.id, shell.width),
            AnsiCodes.reset,
            sep=''
        )
        print(AnsiCodes.yellow, end='')
        Table(
            columns=(Column(''), Column('', Column.Grow)),
            spacing=4,
            header=False,
            width=shell.width
        ).extend(*[
            (' ' + c.name.ljust(name_col_width - 1), c.brief or '')
            for c in topic.commands
        ]).write(sys.stdout)
        print(AnsiCodes.reset, end='')

    def print_topics(self, shell):
        max_name_width = 0
        for topic in shell.ctx.topics:
            for c in topic.commands:
                max_name_width = max(len(c.name), max_name_width)

        for c in shell.ctx.uncat_topic.commands:
            max_name_width = max(len(c.name), max_name_width)

        addl = []
        for topic in shell.ctx.topics:
            if topic.content or not topic.commands:
                addl.append(topic)

            if topic.commands:
                self.print_topic_commands(shell, topic,
                                          name_col_width=max_name_width)
                print()

        if shell.ctx.uncat_topic.commands:
            self.print_topic_commands(shell, shell.ctx.uncat_topic,
                                      name_col_width=max_name_width)
            print()

        if addl:
            addl = sorted(addl, key=lambda x: x.id)
            print(
                AnsiCodes.yellow,
                title_str("Additional Topics", shell.width),
                sep=''
            )
            Table(
                columns=(Column(''), Column('', Column.Grow)),
                spacing=4,
                header=False,
                width=shell.width
            ).extend(*[
                (' ' + topic.id.ljust(max_name_width - 1), topic.name or '')
                for topic in addl
            ]).write(sys.stdout)
            print(AnsiCodes.reset)

    def print_topic(self, shell, id):
        if id not in shell.ctx.topic_lookup:
            if id in shell.commands:
                cmd = shell.commands[id]
                print(AnsiCodes.yellow, cmd.usage, AnsiCodes.reset, sep='')
                return 0

            self.error(shell, "unknown topic: ", id)
            return -1

        topic = shell.ctx.topic_lookup[id]
        if topic.content:
            print(title_str(topic.name or topic.id, shell.width))
            try:
                cnt = topic.content.format(**self.vars)
            except:
                cnt = topic.content

            print(cnt)
            print()

        if topic.commands:
            self.print_topic_commands(shell, topic, "Commands")
        return 0

    def run(self, shell, args):
        if shell.ctx.topics_dirty:
            self.reload(shell)

        try:
            ns = self.parser.parse_args(args)
        except CommandShortCircuit as e:
            return e.code

        rc = 0
        if not ns.topic:
            self.print_topics(shell)
        else:
            rc = self.print_topic(shell, ns.topic)

        return rc
