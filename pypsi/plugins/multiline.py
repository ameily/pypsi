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

from pypsi.base import Plugin
from pypsi.cmdline import StringToken


class MultilinePlugin(Plugin):
    '''
    Provides the ability to input and execute multiline statements. Input lines
    that end in the escape character ``\`` can be continued on the subsequent
    input line. This allows for the user to type the following and produces the
    the statement:

    | ``echo this is a multiline \``
    | ``statement``

    `=>`

    ``echo this is a multiline statement``
    '''

    def __init__(self, prompt='> ', preprocess=30, **kwargs):
        '''
        :param str prompt: the prompt when recording a multiline statement
        '''

        super(MultilinePlugin, self).__init__(preprocess=preprocess, **kwargs)
        self.prompt = prompt
        self.orig_prompt = None
        self.buffer = None

    def setup(self, shell):
        pass

    def set_ml_prompt(self, shell):
        self.orig_prompt = shell.prompt
        shell.prompt = self.prompt

    def reset_prompt(self, shell):
        if self.orig_prompt:
            shell.prompt = self.orig_prompt
            self.orig_prompt = ''

    def on_tokenize(self, shell, tokens, origin):
        if origin != 'input':
            return tokens

        if not tokens:
            if self.buffer:
                self.reset_prompt(shell)
                ret = self.buffer
                self.buffer = None
                return ret
            else:
                return tokens

        if not isinstance(tokens[-1], StringToken):
            return self.buffer + tokens if self.buffer else tokens

        last = tokens[-1]
        if last.escape:
            last.text = last.text[:-1]
            if self.buffer:
                self.buffer.extend(tokens)
            else:
                self.set_ml_prompt(shell)
                self.buffer = tokens

            tokens = None
        elif self.buffer:
            tokens = self.buffer + tokens
            self.buffer = None
            self.reset_prompt(shell)

        return tokens

    def on_input_canceled(self, shell):
        self.reset_prompt(shell)
        self.buffer = None
