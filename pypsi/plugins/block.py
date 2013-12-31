
from pypsi.base import Command, Plugin


class BlockCommand(Command):

    def __init__(self, prompt='> ', **kwargs):
        super(BlockCommand, self).__init__(**kwargs)
        self.prompt = prompt

    def begin_block(self, shell):
        plugin = shell.ctx.block
        plugin.begin_block(shell, self)
        self.old_prompt = shell.prompt
        shell.prompt = self.prompt

    def end_block(self, shell, lines):
        raise NotImplementedError()


class BlockPlugin(Plugin):

    def __init__(self, end_cmd='end', preprocess=20, **kwargs):
        super(BlockPlugin, self).__init__(preprocess=preprocess, **kwargs)
        self.end_cmd = end_cmd
        self.block = None

    def setup(self, shell):
        if 'block' not in shell.ctx:
            shell.ctx.block = self
        return 0

    def on_input(self, shell, line):
        if self.block is not None:
            if line.strip() == self.end_cmd:
                self.end_block(shell)
            else:
                self.block['lines'].append(line)
            return ''
        return line

    def begin_block(self, shell, cmd):
        self.block = {
            'cmd': cmd,
            'lines': []
        }
        return 0

    def end_block(self, shell):
        shell.prompt = self.block['cmd'].old_prompt
        self.block['cmd'].end_block(shell, self.block['lines'])
        self.block = None
        return 0
