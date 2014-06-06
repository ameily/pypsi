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
import subprocess

SystemUsage = """usage: {name} command

execute a system shell command

positional arguments:
  COMMAND            command to execute"""


class SystemCommand(Command):
    '''
    Execute a command on the parent shell. This command can be used as the
    shell's fallback command.
    '''

    def __init__(self, name='system', topic='shell', **kwargs):
        super(SystemCommand, self).__init__(
            name=name,
            topic=topic,
            brief='execute a system shell command',
            usage=SystemUsage.format(name=name),
            **kwargs
        )

    def run(self, shell, args, ctx):
        rc = None
        proc = None
        try:
            if shell.real_stdin == ctx.stdin:
                proc = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)
            else:
                proc = subprocess.Popen(args, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=ctx.stderr, shell=True)
                buff = ctx.stdin.read()
                if isinstance(buff, str):
                    buff = buff.encode('utf-8')

                proc.stdin.write(buff)
                proc.stdin.close()
        except OSError as e:
            if e.errno == 2:
                self.error(shell, "executable not found")
            else:
                self.error(shell, str(e))
            return -1

        for line in proc.stdout:
            ctx.stdout.write(line.decode('utf-8'))
        rc = proc.wait()
        return rc if rc <= 0 else -1

    def fallback(self, shell, name, args, ctx):
        '''
        Pass the command to the parent shell.
        '''
        args.insert(0, name)
        return self
