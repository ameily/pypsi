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

from pypsi.base import Command, PypsiArgParser
from pypsi.format import Table, Column, FixedColumnTable, title_str, word_wrap
from pypsi.stream import AnsiStderr
import sys


class Topic(object):

    def __init__(self, id, name='', content='', commands=None):
        self.id = id
        self.name = name
        self.content = content
        self.commands = commands or []


class HelpCommand(Command):
    '''
    Provides access to manpage-esque topics and command usage information.
    '''

    def __init__(self, name='help', topic='shell', brief='print information on a topic or command', topics=None, **kwargs):
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

    def reload(self, shell):
        self.uncat.commands = []
        for id in self.lookup:
            self.lookup[id].commands = []

        for (name, cmd) in shell.commands.items():
            if cmd.topic:
                if cmd.topic in self.lookup:
                    self.lookup[cmd.topic].commands.append(cmd)
                else:
                    self.add_topic(Topic(cmd.topic, commands=[cmd]))
            else:
                self.uncat.commands.append(cmd)
        self.dirty = False


    def add_topic(self, topic):
        self.dirty = True
        self.lookup[topic.id] = topic
        self.topics.append(topic)

    def print_topic_commands(self, shell, topic, title=None):
        print(title_str(title or topic.name or topic.id, shell.width))
        Table(
            columns=(Column(''), Column('', Column.Grow)),
            spacing=4,
            header=False,
            width=shell.width
        ).extend(
            *[(c.name, c.brief or '') for c in topic.commands]
        ).write(sys.stdout)

    def print_topics(self, shell):
        addl = []
        for topic in self.topics:
            if topic.content or not topic.commands:
                addl.append(topic)

            if topic.commands:
                self.print_topic_commands(shell, topic)
                print()

        if self.uncat.commands:
            self.print_topic_commands(shell, self.uncat)
            print()

        if addl:
            print(title_str("Additional Topics", shell.width))
            tbl = FixedColumnTable([shell.width // 3] * 3)
            for topic in addl:
                tbl.add_cell(sys.stdout, topic.id)
            tbl.flush(sys.stdout)
            print()

    def print_topic(self, shell, id):
        if id not in self.lookup:
            if id in shell.commands:
                cmd = shell.commands[id]
                print(AnsiStderr.yellow, cmd.usage, AnsiStderr.reset, sep='')
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

        ns = self.parser.parse_args(shell, args)
        if self.parser.rc is not None:
            return self.parser.rc

        rc = 0
        if not ns.topic:
            self.print_topics(shell)
        else:
            rc = self.print_topic(shell, ns.topic)

        return rc
