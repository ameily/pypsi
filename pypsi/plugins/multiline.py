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

from pypsi.core import Plugin
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
