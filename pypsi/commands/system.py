
from pypsi.base import Command
import subprocess


class SystemCommand(Command):

    def __init__(self, name='system', **kwargs):
        super(SystemCommand, self).__init__(name=name, **kwargs)

    def run(self, shell, args, ctx):
        rc = None
        proc = None
        if shell.real_stdin == ctx.stdin:
            proc = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        else:
            proc = subprocess.Popen(args, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            proc.stdin.write(ctx.stdin.read())
            proc.stdin.close()

        for line in iter(proc.stdout.readline, ''):
            ctx.stdout.write(line)
        rc = proc.wait()
        return rc
