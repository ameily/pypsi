#
# Copyright (c) 2021, Adam Meily <meily.adam@gmail.com>
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

import sys
from typing import List
from pypsi.core import Command, PypsiArgParser, CommandShortCircuit
from pypsi.table import Table
from pypsi.ansi import Color, ansi_title
from pypsi.shell import Shell


class Topic:

    def __init__(self, name: str, title: str = None, content: str = None,
                 commands: List[str] = None):
        self.name = name or ''
        self.title = title or ''
        self.content = content or ''
        self.commands = commands or []


class HelpCommand(Command):
    '''
    Provides access to manpage-esque topics and command usage information.
    '''

    def __init__(self, name='help', topic='shell', topics=None, **kwargs):
        brief = 'print information on a topic or command'
        self.parser = PypsiArgParser(prog=name, description=brief)

        # Add a callback to self.complete_topics so tab-complete can
        # return the possible topics you may get help on
        self.parser.add_argument("topic", metavar="TOPIC", help="command or topic to print",
                                 nargs='?', completer=self.complete_topics)

        super().__init__(name=name, brief=brief, usage=self.parser.format_help(), topic=topic,
                         **kwargs)

        self.topics = topics

    def setup(self, shell: Shell) -> None:
        shell.ctx.topics = list(self.topics or [])
        shell.ctx.uncat_topic = Topic('uncat', 'Uncategorized Commands & Topics')
        shell.ctx.topic_lookup = {topic.name: topic for topic in shell.ctx.topics}
        shell.ctx.topics_dirty = True

    def complete_topics(self, shell: Shell, args: List[str], prefix: str)  -> List[str]:
        # pylint: disable=unused-argument
        completions = [x.name for x in shell.ctx.topics if x.name.startswith(prefix) or not prefix]

        completions.extend([x for x in shell.commands if x.startswith(prefix) or not prefix])
        return sorted(completions)

    def complete(self, shell: Shell, args: List[str], prefix: str) -> List[str]:
        if shell.ctx.topics_dirty:
            self.reload(shell)

        # The command_completer function takes in the parser, automatically
        # completes optional arguments (ex, '-v'/'--verbose') or sub-commands,
        # and complete any arguments' values by calling a callback function
        # with the same arguments as complete if the callback was defined
        # when the parser was created.
        return self.parser.complete(shell, args, prefix)

    def reload(self, shell: Shell) -> None:
        shell.ctx.uncat_topic.commands = []
        for name in shell.ctx.topic_lookup:
            shell.ctx.topic_lookup[name].commands = []

        for (_, cmd) in shell.commands.items():
            if cmd.topic == '__hidden__':
                continue

            if cmd.topic:
                topic = shell.ctx.topic_lookup.get(cmd.topic)
            else:
                topic = shell.ctx.uncat_topic

            if topic:
                topic.commands.append(cmd)
            else:
                self.add_topic(shell, Topic(cmd.topic, commands=[cmd]))

        shell.ctx.topics_dirty = False

        for topic in shell.ctx.topics:
            if topic.commands:
                topic.commands = sorted(topic.commands, key=lambda x: x.name)

    def add_topic(self, shell: Shell, topic: Topic) -> None:
        shell.ctx.topics_dirty = True
        shell.ctx.topic_lookup[topic.name] = topic
        shell.ctx.topics.append(topic)

    def print_topic_commands(self, topic: Topic, title: str = None) -> None:
        print(Color.yellow(ansi_title(title or topic.title or topic.name)))
        print(Color.yellow, end='')
        Table(
            columns=2,
            spacing=4,
            header=False,
            width=sys.stdout.width
        ).extend(*[
            (c.name, c.brief or '') for c in topic.commands
        ]).write(sys.stdout)
        print(Color.reset_all, end='')

    def print_topics(self, shell: Shell) -> int:
        addl = []
        for topic in shell.ctx.topics:
            if topic.content or not topic.commands:
                addl.append(topic)

            if topic.commands:
                self.print_topic_commands( topic)
                print()

        if shell.ctx.uncat_topic.commands:
            self.print_topic_commands(shell.ctx.uncat_topic)
            print()

        if addl:
            addl = sorted(addl, key=lambda x: x.name)
            print(Color.yellow(ansi_title('Additional Topics')))
            print(Color.yellow, end='')
            Table(
                columns=2,
                spacing=4,
                header=False,
                width=sys.stdout.width
            ).extend(*[
                (topic.name, topic.title or '')
                for topic in addl
            ]).write(sys.stdout)
            print(Color.fg_reset)

        return 0

    def print_topic(self, shell: Shell, name: str) -> int:
        topic = shell.ctx.topic_lookup.get(name)
        command = shell.commands.get(topic)
        if command:
            cmd = shell.commands[id]
            print(Color.yellow(cmd.usage))
            return 0

        if not topic:
            self.error(f'unknown topic: {name}')
            return 1

        if topic.content:
            print(ansi_title(topic.title or topic.name))
            print(topic.content)

        if topic.commands:
            self.print_topic_commands(topic, "Commands")

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
            rc = self.print_topics(shell)
        else:
            rc = self.print_topic(shell, ns.topic)

        return rc
