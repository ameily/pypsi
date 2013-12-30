
from pypsi.base import Command
import subprocess

class SystemCommand(Command):

    def __init__(self, name='system', topic='shell', **kwargs):
        super(SystemCommand, self).__init__(name=name, topic=topic, brief='execute a system shell command', **kwargs)

    def run(self, shell, args, ctx):
        rc = None
        proc = None
        try:
            if shell.real_stdin == ctx.stdin:
                proc = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=ctx.stderr)
            else:
                proc = subprocess.Popen(args, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=ctx.stderr)
                buff = ctx.stdin.read()
                if isinstance(buff, str):
                    buff = buff.encode('utf-8')

                proc.stdin.write(buff)
                proc.stdin.close()
        except OSError as e:
            if e.errno == 2:
                shell.error(self.name, ": executable not found\n")
                return -1

        for line in proc.stdout:
            ctx.stdout.write(line.decode('utf-8'))
        rc = proc.wait()
        return rc if rc <= 0 else -1

    def fallback(self, shell, name, args, ctx):
        args.insert(0, name)
        return self
