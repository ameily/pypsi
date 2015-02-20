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

'''
Provides functions and classes for dealing with command line input, output, and
ansi codes.
'''


def ansi_len(value):
    '''
    Get the length of the provided `str`, not counting any ansi codes.

    :param str value: the input string
    '''
    count = 0
    esc_code = False
    for c in value:
        if c == '\x1b':
            esc_code = True
        elif esc_code:
            if c in 'ABCDEFGHJKSTfmnsulh':
                esc_code = False
        else:
            count += 1
    return count

def ansi_center(s, width):
    '''
    Center the provided string for a given width.

    :param str s: the input string
    :param int width: the desired field width
    '''
    count = ansi_len(s)
    if count >= width:
        return s
    diff = (width - count) // 2
    space = (' '*diff)
    return space + s + space

def ansi_ljust(s, width):
    '''
    Left justify an input string, ensuring that it contains width charaters.

    :param str s: the input string
    :param int width: the desired output width
    :returns str: the output string
    '''
    count = ansi_len(s)
    if count >= width:
        return s
    diff = width - count
    return s + (' ' * diff)

def ansi_rjust(s, width):
    '''
    Right justify the input string.

    :param str s: the input string
    :param int width: the desired width
    :returns str: the output string
    '''
    count = ansi_len(s)
    if count >= width:
        return s
    diff = width - count
    return (' '*diff) + s

def get_lines(txt):
    '''
    Break text to individual lines.

    :returns tuple: a tuple containing the next line and whether the line
        contained a newline charater.
    '''

    if not txt:
        return iter([])

    start = 0
    try:
        while True:
            i = txt.index('\n', start)
            yield (txt[start:i], True)
            start = i + 1
            if start >= len(txt):
                break
    except:
        yield (txt[start:], False)


def wrap_line(txt, width):
    '''
    Word wrap a single line.

    :param str txt: the line to wrap
    :param int width: the maximum width of a wrapped line
    :returns str: the next wrapped line
    '''
    if width <= 0:
        yield txt
    else:
        start = 0
        count = 0
        i = 0
        total = len(txt)
        while i < total:
            esc_code = False
            prev = None
            while count <= width and i < total:
                c = txt[i]
                if c == '\x1b':
                    esc_code = True
                elif esc_code:
                    if c in 'ABCDEFGHJKSTfmnsulh':
                        esc_code = False
                else:
                    count += 1
                    if c in ' \t':
                        prev = i
                i += 1

            if i >= total:
                prev = i
            else:
                prev = prev or i

            yield txt[start:prev]

            start = prev
            while start < total and txt[start] in '\t ':
                start += 1

            i = start
            count = 0

        if count:
            yield txt[start:]


def highlight(target, term, color='1;32'):
    '''
    Find and highlight a term inside of a block of text.

    :param str target: the text to search in
    :param str term: the term to search for
    :param str color: the color to output when the term is found
    :returns str: the input string with all occurrences of the term highlighted
    '''
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
        ret += '\x1b[{color}m{term}\x1b[0m'.format(color=color, term=target[end:end+len(term)])
        start = end + len(term)
        end = s.find(t, start)

    ret += target[start:]
    return ret


def file_size_str(value):
    '''
    Get the human readable file size string from a number. This will convert a
    value of 1024 to 1Kb and 1048576 to 1Mb.

    :param int value: the value to convert
    :returns str: the human readable file size string
    '''
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
    ## TODO, remove stream
    tmpl = "{blue}{type}({reset} {value} {blue}){reset}"
    format_value = None
    if stream:
        format_value = lambda t, v: stream.ansi_format(tmpl, type=t, value=v)
    else:
        tmpl = "{type}( {value} )"
        format_value = lambda t, v: tmpl.format(type=t, value=v)

    if isinstance(obj, bool):
        return format_value("bool", obj)
    elif isinstance(obj, int):
        return format_value("int", "{:d}".format(obj))
    elif isinstance(obj, float):
        return format_value("float", "{:g}".format(obj))
    elif isinstance(obj, (list, tuple)):
        if max_children > 0 and len(obj) > max_children:
            obj = [o for o in obj[:max_children]]
            obj.append('...')

        return format_value(
            "list",
            ', '.join([obj_str(child, max_children=max_children, stream=stream) for child in obj])
        )
    elif obj == None:
        return stream.ansi_format("{blue}<null>{reset}") if stream else "<null>"
    elif isinstance(obj, str):
        return obj
    return str(obj)


def title_str(title, width=80, align='left', hr='=', box=False):
    '''

    '''
    lines = []
    if box:
        border = '+' + ('-'*(width-2)) + '+'
        t = None
        if align == 'left':
            t = ansi_ljust(title, width-4)
        elif align == 'center':
            t = ansi_center(title, width-4)
        else:
            t = ansi_rjust(title, width-4)

        lines.append(border)
        lines.append('| ' + t + ' |')
        lines.append(border)
    else:
        if align == 'left':
            lines.append(title)
        elif align == 'center':
            lines.append(ansi_center(title, width))
        elif align == 'right':
            lines.append(ansi_rjust(title, width))
        lines.append(hr * width)
    return '\n'.join(lines)



class Table(object):
    '''
    Variable width table.
    '''

    def __init__(self, columns, width=80, spacing=1, header=True):
        '''
        :param multiple columns: a list of either class:`Column` instances or a
            single `int` defining how many columns to create
        :param int width: the maximum width of the entire table
        :param int spacing: the amount of space characters to display between
            columns
        :param bool header: whether to display header row with the column names
        '''
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
        '''
        Add a row to the table.

        :param list args: the column values
        '''
        self.rows.append(args)
        for (col, value) in zip(self.columns, args):
            col.width = max(col.width, ansi_len(str(value)))
        return self

    def extend(self, *args):
        '''
        Add multiple rows to the table, each argument should be a list of column
        values.
        '''
        for row in args:
            self.append(*row)
        return self

    def write(self, fp):
        '''
        Print the table to a specified file stream.

        :param file fp: output stream
        '''
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
                if(ansi_len(value) <= col.width):
                    fp.write(ansi_ljust(value, col.width))
                else:
                    wrapped_line = [line for line in wrap_line(value, col.width)]
                    #word_wrap(value, col.width).split('\n')
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
        if (total + self.spacing * (len(self.columns)-1)) > self.width:
            self.columns[-1].mode = Column.Grow

        for col in self.columns:
            if col.mode == Column.Grow:
                remaining = self.width - ((len(self.columns)-1)*self.spacing) - total
                col.width += remaining

        if self.header:
            i = 0
            for col in self.columns:
                if i > 0:
                    fp.write(' ' * self.spacing)
                fp.write(ansi_ljust(col.text, col.width))
                i += 1

            fp.write('\n')
            fp.write('='*self.width)
            fp.write('\n')

        for row in self.rows:
            write_overflow(row)

        return 0




class Column(object):
    '''
    A table column.
    '''

    #: Size mode to have the column shrink to its contents
    Shrink = 0
    #: Size mode to have the column grow to the maximum width it can have
    Grow = 1

    def __init__(self, text='', mode=0):
        '''
        :param str text: the column name
        :param int mode: the column size mode
        '''
        self.text = text
        self.mode = mode
        self.width = ansi_len(text)


class FixedColumnTable(object):
    '''
    A table that has preset column widths.
    '''

    def __init__(self, widths):
        '''
        :param list widths: the list of column widths (`int`)
        '''
        self.widths = [int(width) for width in widths]
        self.buffer = []

    def write_row(self, fp, *args):
        '''
        Print a single row.

        :param file fp: the output file stream (usually sys.stdout or sys.stderr)
        :param list args: the column values for the row
        '''
        for (width, value) in zip(self.widths, args):
            fp.write(ansi_ljust(value, width))
            #diff = width - len(value)
            #if diff > 0:
            #    fp.write(' ' * diff)
        fp.write('\n')

    def add_cell(self, fp, col):
        '''
        Add a single cell to the table. The current row is printed if the column
        completes the row.
        '''
        self.buffer.append(col)
        if len(self.buffer) == len(self.widths):
            self.write_row(fp, *self.buffer)
            self.buffer = []

    def flush(self, fp):
        '''
        Force a write of the table.

        :param file fp: the output file stream
        '''
        if self.buffer:
            self.write_row(fp, *self.buffer)
            self.buffer = []
