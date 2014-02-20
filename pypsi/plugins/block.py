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

from pypsi.base import Command, Plugin


class BlockCommand(Command):
    '''
    Base class for any block commands that accept multiple statements from the
    user. Block commands allow the user to input several individual statement
    lines and postpone processing and execution until a later time. For example,
    the :class:`pypsi.commands.macro.MacroCommand` is a block command that
    allows the user to record several statements and then execute them when the
    macro is called.
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
    terminated the user inputs the value of :data:`end_cmd`, at which point, the
    active :class:`BlockCommand` is retrieved and :meth:`BlockCommand.end_block`
    is called.
    '''

    def __init__(self, end_cmd='end', preprocess=20, **kwargs):
        '''
        :param str end_cmd: the statement that will terminate the active block
        '''
        super(BlockPlugin, self).__init__(preprocess=preprocess, **kwargs)
        self.end_cmd = end_cmd

    def setup(self, shell):
        '''
        Adds a reference to this instance in the shell's context. Allows plugins
        and commands to get this plugin by accessing ``shell.ctx.block``.
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
        shell.ctx.recording_block['cmd'].end_block(shell, shell.ctx.recording_block['lines'])
        shell.ctx.recording_block = None
        return 0

    def on_input_canceled(self, shell):
        if shell.ctx.recording_block is not None:
            shell.ctx.recording_block['cmd'].cancel_block(shell)
            shell.prompt = shell.ctx.recording_block['cmd'].old_prompt
            shell.ctx.recording_block = None

