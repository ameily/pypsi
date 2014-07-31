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


class CommentPlugin(Plugin):
    '''
    Allow inline comments in statements. Tokens that begin with ``prefix`` will
    be removed from the statement and so will subsequent tokens. This allows for
    statements like the following:

    | ``pypsi )> echo hello  # print hello to the screen``
    | ``hello``
    | ``pypsi )> # this is a whole line comment``
    | ``pypsi )>``
    '''

    def __init__(self, preprocess=20, prefix='#', **kwargs):
        '''
        :param str prefix: the character(s) to begin a comment
        '''
        super(CommentPlugin, self).__init__(preprocess=preprocess, **kwargs)
        self.prefix = prefix

    def setup(self, shell):
        pass

    def on_tokenize(self, shell, tokens, origin):
        index = 0
        for token in tokens:
            if isinstance(token, StringToken) and token.text.startswith(self.prefix) and not token.quote:
                break
            index += 1

        return tokens[:index] if index else None
