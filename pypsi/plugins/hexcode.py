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


class HexCodePlugin(Plugin):
    '''
    Allows the user to input hex code escape sequences. Hex code sequences will
    be converted to a raw UTF8 character after processing. Escape sequences are
    in the format of: ``\\xDD``, where ``DD`` is a 2-digit hex value. This
    plugin can be used, for example, to print ANSI escape codes to the screen.
    To print the color red, for example, the user would input the sequence
    ``\\x1b[1;31m``.
    '''

    def __init__(self, preprocess=5, **kwargs):
        super(HexCodePlugin, self).__init__(preprocess=preprocess, **kwargs)

    def on_tokenize(self, shell, tokens, origin):
        escape_char = shell.features.escape_char
        for token in tokens:
            if (not isinstance(token, StringToken) or
                    escape_char not in token.text):
                continue

            escape = False
            hexcode = None
            text = ''
            for c in token.text:
                if escape:
                    escape = False
                    if c == 'x':
                        hexcode = ''
                    else:
                        text += escape_char + c
                elif hexcode is not None:
                    hexcode += c
                    if len(hexcode) == 2:
                        try:
                            hexcode = int(hexcode, base=16)
                            text += chr(hexcode)
                            hexcode = None
                        except ValueError:
                            text += '\\x' + hexcode
                            hexcode = None
                elif c == escape_char:
                    escape = True
                else:
                    text += c

            if hexcode:
                text += '\\x' + hexcode

            if escape:
                text += escape_char

            token.text = text
        return tokens
