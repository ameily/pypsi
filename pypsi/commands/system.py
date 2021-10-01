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

from typing import List
import subprocess
import errno
import sys
from pypsi.shell import Shell
from pypsi.core import Command


SystemUsage = """usage: {name} COMMAND

execute a system shell command

positional arguments:
  COMMAND            command to execute"""


class SystemCommand(Command):
    '''
    Execute a command on the parent shell. This command can be used as the
    shell's fallback command.
    '''

    def __init__(self, name='system', topic='shell', use_shell=False,
                 **kwargs):
        super().__init__(name=name, topic=topic, brief='execute a system shell command',
                         usage=SystemUsage.format(name=name), **kwargs)
        self.use_shell = use_shell

    def run(self, shell: Shell, args: List[str]) -> int:
        rc = None

        if not args:
            self.usage_error('missing required argument: COMMAND')
            return 1

        try:
            proc = subprocess.Popen(args, stdout=sys.stdout.thread_local_get(),
                                    stdin=sys.stdin.thread_local_get(),
                                    stderr=sys.stderr.thread_local_get(),  shell=self.use_shell)
        except OSError as e:
            if e.errno == errno.ENOENT:
                self.error(f'{args[0]}: command not found')
            else:
                self.error(f'{args[0]}: {e.strerror}')
            return e.errno or -1

        try:
            rc = proc.wait()
        except KeyboardInterrupt:
            proc.kill()
            proc.communicate()
            rc = proc.wait() or -1

        return rc

    def fallback(self, shell: Shell, name: str, args: List[str]) -> int:
        '''
        Pass the command to the parent shell.
        '''
        args.insert(0, name)
        return self.run(shell, args)
