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
from pypsi.format import Table, Column, FixedColumnTable, title_str
from pypsi.stream import AnsiCodes
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

        self.parser.add_argument(
            "topic", metavar="TOPIC", help="command or topic to print",
            nargs='?'
        )

        super(HelpCommand, self).__init__(
            name=name, brief=brief, usage=self.parser.format_help(),
            topic=topic, **kwargs
        )

        self.vars = vars or {}
        self.topics = topics

    def setup(self, shell):
        shell.ctx.topics = list(self.topics or [])
        shell.ctx.uncat_topic = Topic('uncat', 'Uncategorized Commands & Topics')
        shell.ctx.topic_lookup = {t.id: t for t in shell.ctx.topics}
        shell.ctx.topics_dirty = True

    def complete(self, shell, args, prefix):
        #pre = args[-1] if args else prefix
        if shell.ctx.topics_dirty:
            self.reload(shell)

        completions = [x.id for x in shell.ctx.topics if x.id.startswith(prefix) or not prefix]
        completions.extend([x for x in shell.commands if x.startswith(prefix) or not prefix])
        completions = sorted(completions)
        
        return completions

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

    def print_topic_commands(self, shell, topic, title=None, name_col_width=20):
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
        #).extend(
        #    *[
        #        (' Name', 'Description'),
        #        (' ----', '-----------')
        #    ]
        ).extend(
            *[(' '+c.name.ljust(name_col_width - 1), c.brief or '') for c in topic.commands]
        ).write(sys.stdout)
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
                self.print_topic_commands(shell, topic, name_col_width=max_name_width)
                print()

        if shell.ctx.uncat_topic.commands:
            self.print_topic_commands(shell, shell.ctx.uncat_topic, name_col_width=max_name_width)
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
            ).extend(
                *[(' '+topic.id.ljust(max_name_width - 1), topic.name or '') for topic in addl]
            ).write(sys.stdout)
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

    def run(self, shell, args, ctx):
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
