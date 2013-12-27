
from pypsi.base import Command
import os


class IncludeFile(object):

    def __init__(self, path, line=1):
        self.name = os.path.basename(path)
        self.abspath = os.path.abspath(path)
        self.line = line


class IncludeCommand(Command):

    def __init__(self, name='include', topic='shell', **kwargs):
        super(IncludeCommand, self).__init__(name=name, topic=topic, brief='execute a script file', **kwargs)
        self.stack = []

    def run(self, shell, args, ctx):
        if len(args) != 1:
            return 1

        fp = None
        ifile = IncludeFile(args[0])

        top = False
        templ = ''
        if self.stack:
            templ = shell.error.prefix
            for i in self.stack:
                if i.abspath == ifile.abspath:
                    shell.error("recursive include for file ", ifile.abspath, '\n')
                    return -1
        else:
            templ = shell.error.prefix + "error in file {file} on line {line}: "
            top = True

        self.stack.append(ifile)

        try:
            fp = open(args[0], 'r')
        except (OSError, IOError) as e:
            shell.error("error opening file ", args[0], ": ", str(e), '\n')
            return -1

        orig_prefix = shell.error.prefix
        next = ctx.fork()
        for line in fp:
            shell.error.prefix = templ.format(file=ifile.name, line=ifile.line)
            shell.execute(line.strip(), next)
            ifile.line += 1

        if top:
            shell.error.prefix = orig_prefix

        self.stack.pop()
        fp.close()

        return 0
