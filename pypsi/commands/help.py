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

from pypsi.base import Command
from pypsi.utils import Title


class HelpCommand(Command):
    '''
    Provides access to manpage-esque topics and command usage information.
    '''

    def __init__(self, name='help', topic='shell', topics=None, **kwargs):
        super(HelpCommand, self).__init__(
            name=name, brief='print help on a topic or command', usage='',
            topic=topic, **kwargs
        )
        self.order =[i[0] for i in topics] if topics else []
        self.topics = {i[0]: i[1] for i in topics} if topics else {}

    def add_topic(self, name, text):
        pass

    def print_cmd(self, shell, cmd, name_width):
        shell.warn(cmd.name, ' ' * (name_width - len(cmd.name)), '    ', cmd.brief, '\n')

    def print_commands(self, shell, print_topic=None):
        if self.topics:
            col1 = 0
            sections = {i: [] for i in self.order}
            for (name, cmd) in shell.commands.items():
                topic = cmd.topic if cmd.topic in self.topics else 'misc'
                if print_topic and print_topic != cmd.topic:
                    continue

                col1 = max(col1, len(name))
                sections[topic].append(cmd)

            first = True
            for topic in self.order:
                if print_topic and print_topic != topic:
                    continue

                if first:
                    first = False
                else:
                    shell.warn('\n')

                shell.warn(Title("{} Commands".format(self.topics[topic])))

                cmds = sorted(sections[topic], key=lambda i: i.name)
                for cmd in cmds:
                    self.print_cmd(shell, cmd, col1)
        else:
            col1 = 0
            cmds = []
            for (name, cmd) in shell.commands.items():
                col1 = max(col1, len(name))
                cmds.append(cmd)
            cmds = sorted(cmds, key=lambda x: x.name)
            for cmd in cmds:
                self.print_cmd(shell, cmd, col1)

    def run(self, shell, args, ctx):
        if not args:
            self.print_commands(shell)
        elif len(args) > 1:
            return 1
        elif args[0] in self.topics:
            self.print_commands(shell, args[0])
        else:
            if args[0] in shell.commands:
                usage = shell.commands[args[0]].usage
                if usage and callable(usage):
                    msg = usage()
                    if isinstance(msg, str) and msg:
                        shell.warn(msg)
                        if msg[-1] != '\n':
                            shell.warn('\n')
                else:
                    shell.warn(usage or 'No help information', '\n')
            else:
                shell.error("No help for topic ", args[0], '\n')

        return 0
