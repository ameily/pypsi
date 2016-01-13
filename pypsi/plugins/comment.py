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


class CommentPlugin(Plugin):
    '''
    Allow inline comments in statements. Tokens that begin with ``prefix`` will
    be removed from the statement and so will subsequent tokens. This allows
    for statements like the following:

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
            if (isinstance(token, StringToken) and
                    token.text.startswith(self.prefix) and
                    not token.quote):
                break
            index += 1

        return tokens[:index] if index else None
