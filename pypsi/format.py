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


def word_wrap(text, width, prefix=None, multiline=True):
    if multiline and '\n' in text:
        parts = text.split('\n')
        return '\n'.join([word_wrap(t, width, prefix, False) for t in parts])

    if len(text) < width:
        return text

    plen = len(prefix) if prefix else 0

    lines = []
    start = 0
    count = len(text)
    while start < count:
        end = (start + width) - plen
        line = None
        if end >= count or text[end].isspace():
            line = text[start:end]
            start = end
        else:
            line_end = end
            for i in range(end, start-1, -1):
                if text[i].isspace():
                    line_end = i
                    break
            line = text[start:line_end]
            start = line_end

        while start < count:
            if text[start].isspace():
                start+=1
            else:
                break

        if lines and prefix:
            line = line.strip()
            lines.append(prefix+line)
        else:
            lines.append(line)

    return '\n'.join(lines)


def highlight(target, term, color='1;32'):
    if not color:
        return target

    s = target.lower()
    t = term.lower()
    #print("term:", term)
    start = 0

    end = s.find(t)
    ret = ''
    while end >= 0:
        ret += target[start:end]
        ret += '\x1b[{color}m{term}\x1b[1;0m'.format(color=color, term=target[end:end+len(term)])
        start = end + len(term)
        end = s.find(t, start)

    ret += target[start:]
    return ret


def file_size_str(value):
    value = float(value)
    units = ['Kb', 'Mb', 'Gb', 'Tb']
    unit = 'B'
    for u in units:
        v = value / 1024.0
        if v < 1.0:
            break
        value = v
        unit = u
    if unit == 'B':
        return "{} B".format(int(value))
    return "{:.2f} {}".format(value, unit)


def obj_str(obj, max_children=3, stream=None):
    wrap_value = null_str = None
    if stream:
        wrap_value = lambda t, v: "{}{}( {}{} {}){}".format(
            stream.blue, t, stream.reset, v, stream.blue,
            stream.reset
        )
        null_str = "{}<null>{}".format(stream.blue, stream.reset)
    else:
        wrap_value = lambda t, v: "{}( {} )".format(t, v)
        null_str = "<null>"

    if isinstance(obj, bool):
        return wrap_value("bool", obj)
    elif isinstance(obj, int):
        return wrap_value("int", "{:d}".format(obj))
    elif isinstance(obj, float):
        return wrap_value("float", "{:g}".format(obj))
    elif isinstance(obj, (list, tuple)):
        if max_children > 0 and len(obj) > max_children:
            obj = [o for o in obj[:max_children]]
            obj.append('...')

        return wrap_value(
            "list",
            ', '.join([obj_str(child, max_children=max_children, stream=stream) for child in obj])
        )
    elif obj == None:
        return null_str
    elif isinstance(obj, str):
        return obj
    return str(obj)


def title_str(title, width=80, align='left', hr='=', box=False):
    lines = []
    if box:
        border = '+' + ('-'*(width-2)) + '+'
        t = None
        if align == 'left':
            t = title.ljust(width-4)
        elif align == 'center':
            t = title.center(width-4)
        else:
            t = title.rjust(width-4)

        lines.append(border)
        lines.append('| ' + t + ' |')
        lines.append(border)
    else:
        if align == 'left':
            lines.append(title)
        elif align == 'center':
            #left = ' ' * ((width - len(title)) // 2)
            lines.append(title.center(width))
        elif align == 'right':
            #left = ' ' * (width - len(title))
            lines.append(title.rjust(width))
        lines.append(hr * width)
    return '\n'.join(lines)



class Table(object):
    # TODO: implement field overflow (maybe?)

    def __init__(self, columns, width=80, spacing=1, header=True):
        if isinstance(columns, int):
            self.columns = [Column()] * columns
            header = False
        else:
            self.columns = columns
        self.width = width
        self.spacing = spacing
        self.header = header
        self.rows = []

    def append(self, *args):
        self.rows.append(args)
        for (col, value) in zip(self.columns, args):
            col.width = max(col.width, len(str(value)))
        return self

    def extend(self, *args):
        for row in args:
            self.append(*row)
        return self

    def write(self, fp):
        def write_overflow(row):
            overflow = [''] * len(self.columns)
            column_idx = 0
            for (col, value) in zip(self.columns, row):
                if column_idx > 0:
                    fp.write(' ' * self.spacing)
                if isinstance(value, str):
                    pass
                else:
                    value = str(value)
                if(len(value) <= col.width):
                    fp.write(value.ljust(col.width))
                else:
                    wrapped_line = word_wrap(value, col.width).split('\n')
                    if len(wrapped_line) > 1:
                        overflow[column_idx] = ' '.join(wrapped_line[1:])
                    fp.write(wrapped_line[0])
                # Move to next column
                column_idx += 1
            fp.write('\n')

            # deal with overflowed data
            if ''.join(overflow):
                write_overflow(overflow)

        total = sum([ col.width for col in self.columns ])

        # Resize columns if last too wide
        # TODO: Smarter column resizing, maybe pick widest column
        if total + self.spacing*(len(self.columns)-1) > self.width:
            self.columns[-1].mode = Column.Grow

        for i in range(len(self.columns)):
            col = self.columns[i]
            if col.mode == Column.Grow:
                remaining = self.width - ((len(self.columns)-1)*self.spacing) - total
                col.width += remaining

        if self.header:
            i = 0
            for col in self.columns:
                if i > 0:
                    fp.write(' ' * self.spacing)
                fp.write(col.text.ljust(col.width))
                #fp.write("{{: <{}}}".format(col.width).format(col.text))
                i += 1

            fp.write('\n')
            fp.write('='*self.width)
            fp.write('\n')

        for row in self.rows:
            write_overflow(row)

        return 0




class Column(object):
    Shrink = 0
    Grow = 1

    def __init__(self, text='', mode=0):
        self.text = text
        self.mode = mode
        self.width = len(text)


class FixedColumnTable(object):

    def __init__(self, widths):
        self.widths = [int(width) for width in widths]
        self.buffer = []

    def write_row(self, fp, *args):
        for (width, value) in zip(self.widths, args):
            fp.write(value.ljust(width))
            #diff = width - len(value)
            #if diff > 0:
            #    fp.write(' ' * diff)
        fp.write('\n')

    def add_cell(self, fp, col):
        self.buffer.append(col)
        if len(self.buffer) == len(self.widths):
            self.write_row(fp, *self.buffer)
            self.buffer = []

    def flush(self, fp):
        if self.buffer:
            self.write_row(fp, *self.buffer)
            self.buffer = []
