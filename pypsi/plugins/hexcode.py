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
        for token in tokens:
            if not isinstance(token, StringToken) or '\\' not in token.text:
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
                        text += '\\' + c
                elif hexcode is not None:
                    hexcode += c
                    if len(hexcode) == 2:
                        try:
                            hexcode = int(hexcode, base=16)
                            text += chr(hexcode)
                            hexcode = None
                        except ValueError:
                            text += '\\x' + hexcode
                elif c == '\\':
                    escape = True
                else:
                    text += c

            if hexcode:
                text += '\\x' + hexcode

            if escape:
                text += '\\'

            token.text = text
        return tokens
