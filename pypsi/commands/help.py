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

from pypsi.base import Command, PypsiArgParser, CommandShortCircuit
from pypsi.format import Table, Column, FixedColumnTable, title_str, word_wrap
from pypsi.stream import AnsiStdout
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

    def __init__(self, name='help', topic='shell', brief='print information on a topic or command', topics=None,
                 **kwargs):
        self.parser = PypsiArgParser(
            prog=name,
            description=brief
        )

        self.parser.add_argument(
            "topic", metavar="TOPIC", help="command or topic to print",
            nargs='?'
        )

        super(HelpCommand, self).__init__(
            name=name, brief=brief, usage=self.parser.format_help(),
            topic=topic, **kwargs
        )

        self.topics = list(topics or [])
        self.uncat = Topic('uncat', 'Uncategorized Commands & Features')
        self.lookup = {t.id: t for t in self.topics}
        self.dirty = True

    def complete(self, shell, args, prefix):
        args = [arg for arg in args if not arg.startswith('-')]
        if self.dirty:
            self.reload(shell)

        completions = []
        base = []
        for topic in self.topics:
            base.append(topic.name or topic.id)
            base.extend([command.name for command in topic.commands])

        if len(args) <= 1:
            completions.extend([x for x in base if x.startswith(prefix) or not prefix])

        return sorted(completions)

    def reload(self, shell):
        self.uncat.commands = []
        for id in self.lookup:
            self.lookup[id].commands = []

        for (name, cmd) in shell.commands.items():
            if cmd.topic == '__hidden__':
                continue

            if cmd.topic:
                if cmd.topic in self.lookup:
                    self.lookup[cmd.topic].commands.append(cmd)
                else:
                    self.add_topic(Topic(cmd.topic, commands=[cmd]))
            else:
                self.uncat.commands.append(cmd)
        self.dirty = False
        
        for topic in self.topics:
            if topic.commands:
                topic.commands = sorted(topic.commands, key=lambda x: x.name)

    def add_topic(self, topic):
        self.dirty = True
        self.lookup[topic.id] = topic
        self.topics.append(topic)

    def print_topic_commands(self, shell, topic, title=None, name_col_width=20):
        print(
            AnsiStdout.yellow,
            title_str(title or topic.name or topic.id, shell.width),
            AnsiStdout.reset,
            sep=''
        )
        print(AnsiStdout.yellow, end='')
        Table(
            columns=(Column(''), Column('', Column.Grow)),
            spacing=4,
            header=False,
            width=shell.width
        #).extend(
        #    *[
        #        (' Name', 'Description'),
        #        (' ----', '-----------')
        #    ]
        ).extend(
            *[(' '+c.name.ljust(name_col_width - 1), c.brief or '') for c in topic.commands]
        ).write(sys.stdout)
        print(AnsiStdout.reset, end='')

    def print_topics(self, shell):
        max_name_width = 0
        for topic in self.topics:
            for c in topic.commands:
                max_name_width = max(len(c.name), max_name_width)

        for c in self.uncat.commands:
            max_name_width = max(len(c.name), max_name_width)

        addl = []
        for topic in self.topics:
            if topic.content or not topic.commands:
                addl.append(topic)

            if topic.commands:
                self.print_topic_commands(shell, topic, name_col_width=max_name_width)
                print()

        if self.uncat.commands:
            self.print_topic_commands(shell, self.uncat, name_col_width=max_name_width)
            print()

        if addl:
            addl = sorted(addl, key=lambda x: x.id)
            print(
                AnsiStdout.yellow,
                title_str("Additional Topics", shell.width),
                sep=''
            )
            Table(
                columns=(Column(''), Column('', Column.Grow)),
                spacing=4,
                header=False,
                width=shell.width
            ).extend(
                *[(' '+topic.id.ljust(max_name_width - 1), topic.name or '') for topic in addl]
            ).write(sys.stdout)
            print(AnsiStdout.reset)

    def print_topic(self, shell, id):
        if id not in self.lookup:
            if id in shell.commands:
                cmd = shell.commands[id]
                print(AnsiStdout.yellow, cmd.usage, AnsiStdout.reset, sep='')
                return 0

            self.error(shell, "unknown topic: ", id)
            return -1

        topic = self.lookup[id]
        if topic.content:
            print(title_str(topic.name or topic.id, shell.width))
            print(word_wrap(topic.content, shell.width))
            print()

        if topic.commands:
            self.print_topic_commands(shell, topic, "Commands")
        return 0

    def run(self, shell, args, ctx):
        if self.dirty:
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
