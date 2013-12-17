
from pypsi.base import Plugin, Preprocessor
from pypsi.cmdline import StringToken


class HexCodePlugin(Plugin, Preprocessor):

    def __init__(self, **kwargs):
        super(HexCodePlugin, self).__init__(**kwargs)

    def on_tokenize(self, shell, tokens):
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
            token.text = text
        return tokens
