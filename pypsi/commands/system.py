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

from pypsi.core import Command
import subprocess
import errno
import sys

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
        super(SystemCommand, self).__init__(
            name=name,
            topic=topic,
            brief='execute a system shell command',
            usage=SystemUsage.format(name=name),
            **kwargs
        )
        self.use_shell = use_shell

    def run(self, shell, args):
        rc = None

        try:
            proc = subprocess.Popen(
                args, stdout=sys.stdout._get_target(),
                stdin=sys.stdin._get_target(),
                stderr=sys.stderr._get_target(),
                shell=self.use_shell
            )
        except OSError as e:
            if e.errno == errno.ENOENT:
                self.error(shell, args[0], ": command not found")
            else:
                self.error(shell, args[0], ": ", e.strerror)
            return -e.errno

        try:
            rc = proc.wait()
        except KeyboardInterrupt:
            proc.kill()
            proc.communicate()
            rc = proc.wait()

        return rc

    def fallback(self, shell, name, args):
        '''
        Pass the command to the parent shell.
        '''
        args.insert(0, name)
        return self.run(shell, args)
