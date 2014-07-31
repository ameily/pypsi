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
import os


class ChdirCommand(Command):
    '''
    Change the current working directory. This accepts one of the following:

    * <path> - a relative or absolute path
    * ~ - the current user's home directory
    * ~<user> - <user>'s home directory
    * - - the previous directory
    '''

    def __init__(self, name='cd', brief='change current working directory',
                 topic='shell', **kwargs):
        super(ChdirCommand, self).__init__(name=name, brief=brief, topic=topic, **kwargs)

        self.parser = PypsiArgParser(prog=name, description=brief)
        self.parser.add_argument('path', help='path', metavar="PATH")

    def setup(self, shell):
        shell.ctx.chdir_last_dir = os.getcwd()

    def chdir(self, shell, path, print_cwd=False):
        prev = os.getcwd()
        try:
            os.chdir(path)
            if print_cwd:
                print(os.getcwd())
        except OSError as e:
            self.error(shell, path, ": ", e.strerror)
            return -1
        except Exception as e:
            self.error(shell, path, ": ", str(e))
            return -1

        shell.ctx.chdir_last_dir = prev
        return 0

    def run(self, shell, args, ctx):
        try:
            ns = self.parser.parse_args(args)
        except CommandShortCircuit as e:
            return e.code

        if ns.path == '-':
            return self.chdir(shell, shell.ctx.chdir_last_dir, True)

        if ns.path.startswith('~'):
            return self.chdir(shell, os.path.expanduser(ns.path))

        return self.chdir(shell, ns.path)

