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

import re

# 1;32m
# 2J
# 1;32;1;22m

class TextStyle(object):

    def __init__(self, fg=None, bg=None, clear_screen=None, pos=None, raw=None):
        self.fg = fg
        self.bg = bg
        self.clear_screen = clear_screen
        self.pos = pos
        if raw:
            self.parse(raw)

    def parse(self, txt):
        intense = None
        nums = []
        if txt[-1] == 'm':
            parts = txt[:-1].split(';')
            nums = [int(p) for p in parts]
            for n in nums:
                if n == 1:
                    intense = True
                else:
                    if n >= 30 and n <= 37:
                        self.fg = "intense-" if intense else ''
                        self.fg += str(n)
                    elif n >= 40 and n <= 47:
                        self.bg = 'intense-' if intense else ''
                        self.bg += str(n)
        elif txt[-1] == 'J':
            self.clear_screen = True
        elif txt[-1] == 'H':
            self.pos = 0 #TODO

    def __str__(self):
        cls = []
        
        return ' '.join(cls)


class StyledText(object):

    def __init__(self, text=None, style=None):
        self.text = text
        self.style = style

    def __str__(self):
        return "<span class='{}'>{}</span>".format(self.style, self.text.strip())


class AnsiDecoder(object):
    #ansi_re = '\x1b[(?:(?<num>\\d+)(?:;))*(?<letter>\\w)'
    ansi_re = re.compile('\x1b\\[[0-9;]+\\w')

    def __init__(self):
        pass

    def decode(self, s, current):
        parts = []
        start = 0
        active = StyledText(style=current)
        for m in self.ansi_re.finditer(s):
            if start != m.start():
                active.text = s[start:m.start()]
                parts.append(active)

            start = m.end()
            style = TextStyle(raw=m.group()[2:])
            active = StyledText(style=style)

        active.text = s[start:]
        parts.append(active)
        return parts

    def html(self, s, current, base_cls):
        parts = self.decode(s, current)
        for p in parts:
            cls = [base_cls]
            if p.style.fg:
                '''
                if p.style.fg.startswith('intense-'):
                    cls.append('fg-intense')
                    cls.append('fg-'+p.style.fg[8:])
                else:
                    cls.append("fg-"+p.style.fg)
                '''
                cls.append("fg-"+p.style.fg)
            if p.style.bg:
                cls.append("bg-"+p.style.bg)
            if p.style.clear_screen:
                cls.append("clear-screen")
            txt = p.text.replace("<", "&lt;").replace(">", "&gt;")
            yield ("<span class='{}'>{}</span>".format(' '.join(cls), txt), p.style)


if __name__ == "__main__":
    fp = open("test.txt", 'r')
    s = fp.read()
    fp.close()

    d = AnsiDecoder()
    current = TextStyle()
    parts = d.decode(s, current)
    for p in parts:
        print(str(p))


