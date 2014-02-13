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
from pypsi.utils import safe_open
import os




class IncludeFile(object):

    def __init__(self, path, line=1):
        self.name = os.path.basename(path)
        self.abspath = os.path.abspath(path)
        self.line = line


class IncludeCommand(Command):
    '''
    Execute a script file. This entails reading each line of the given file and
    processing it as if it were typed into the shell.
    '''

    def __init__(self, name='include', topic='shell', **kwargs):
        super(IncludeCommand, self).__init__(name=name, topic=topic, brief='execute a script file', **kwargs)
        self.stack = []

    def run(self, shell, args, ctx):
        if len(args) != 1:
            return 1

        return self.include_file(shell, args[0], ctx)

    def include_file(self, shell, path, ctx):
        fp = None
        ifile = IncludeFile(path)

        top = False
        templ = ''
        if self.stack:
            #templ = shell.error.prefix
            for i in self.stack:
                if i.abspath == ifile.abspath:
                    self.error(shell, "recursive include for file ", ifile.abspath, '\n')
                    return -1
        else:
            #templ = shell.error.prefix + "error in file {file} on line {line}: "
            top = True

        self.stack.append(ifile)

        try:
            fp = safe_open(path, 'r')
        except (OSError, IOError) as e:
            self.error(shell, "error opening file ", path, ": ", str(e), '\n')
            return -1

        #orig_prefix = shell.error.prefix
        next = ctx.fork()
        for line in fp:
            #shell.error.prefix = templ.format(file=ifile.name, line=ifile.line)
            shell.execute(line.strip(), next)
            ifile.line += 1

        #if top:
        #    shell.error.prefix = orig_prefix

        self.stack.pop()
        fp.close()

        return 0
