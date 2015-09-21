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

from pypsi.core import Command, Plugin


class BlockCommand(Command):
    '''
    Base class for any block commands that accept multiple statements from the
    user. Block commands allow the user to input several individual statement
    lines and postpone processing and execution until a later time. For
    example, the :class:`pypsi.commands.macro.MacroCommand` is a block command
    that allows the user to record several statements and then execute them
    when the macro is called.
    '''

    def __init__(self, prompt='> ', **kwargs):
        super(BlockCommand, self).__init__(**kwargs)
        self.prompt = prompt

    def begin_block(self, shell):
        '''
        Begin a block command and record subsequent statements to the block
        buffer.
        '''
        plugin = shell.ctx.block
        plugin.begin_block(shell, self)
        self.old_prompt = shell.prompt
        shell.prompt = self.prompt

    def end_block(self, shell, lines):
        '''
        Called when a block has ended recording. Subclasses must implement this
        method.

        :param pypsi.shell.Shell shell: the active shell
        :param list lines: the list of unprocessed statements (:class:`str`)
        '''
        raise NotImplementedError()


class BlockPlugin(Plugin):
    '''
    Provide the ability to record multiple statements for future processing and
    execution. By itself, the :class:`BlockPlugin` doesn't do anything. Rather,
    new :class:`BlockCommand` are developed that leverage this plugin's
    preprocessor to record multiple statements from the user. Blocks are
    terminated the user inputs the value of :data:`end_cmd`, at which point,
    the active :class:`BlockCommand` is retrieved and
    :meth:`BlockCommand.end_block` is called.
    '''

    def __init__(self, end_cmd='end', preprocess=20, **kwargs):
        '''
        :param str end_cmd: the statement that will terminate the active block
        '''
        super(BlockPlugin, self).__init__(preprocess=preprocess, **kwargs)
        self.end_cmd = end_cmd

    def setup(self, shell):
        '''
        Adds a reference to this instance in the shell's context. Allows
        plugins and commands to get this plugin by accessing
        ``shell.ctx.block``.
        '''
        if 'block' not in shell.ctx:
            shell.ctx.block = self
        if 'recording_block' not in shell.ctx:
            shell.ctx.recording_block = None
        return 0

    def on_input(self, shell, line):
        if shell.ctx.recording_block is not None:
            if line.strip() == self.end_cmd:
                self.end_block(shell)
            else:
                shell.ctx.recording_block['lines'].append(line)
            return None
        return line

    def begin_block(self, shell, cmd):
        '''
        Begin recording a new block.

        :param pypsi.shell.Shell shell: the active shell
        :param BlockCommand cmd: the active block command
        '''
        shell.ctx.recording_block = {
            'cmd': cmd,
            'lines': []
        }
        return 0

    def end_block(self, shell):
        '''
        End the block. Calls the active block command's
        :meth:`BlockCommand.end_block` method.
        '''
        shell.prompt = shell.ctx.recording_block['cmd'].old_prompt
        shell.ctx.recording_block['cmd'].end_block(
            shell, shell.ctx.recording_block['lines']
        )
        shell.ctx.recording_block = None
        return 0

    def on_input_canceled(self, shell):
        if shell.ctx.recording_block is not None:
            shell.ctx.recording_block['cmd'].cancel_block(shell)
            shell.prompt = shell.ctx.recording_block['cmd'].old_prompt
            shell.ctx.recording_block = None
