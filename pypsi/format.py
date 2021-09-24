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

'''
Provides functions and classes for dealing with command line input and output.
'''

from typing import Union
from .ansi import ansi_len

def humanize_file_size(value: Union[int, float]) -> str:
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
        Add multiple rows to the table, each argument should be a list of
        column values.
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
                if ansi_len(value) <= col.width:
                    fp.write(ansi_ljust(value, col.width))
                else:
                    wrapped_line = list(wrap_line(value, col.width))
                    if len(wrapped_line) > 1:
                        overflow[column_idx] = ' '.join(wrapped_line[1:])
                    fp.write(wrapped_line[0])
                # Move to next column
                column_idx += 1
            fp.write('\n')

            # deal with overflowed data
            if ''.join(overflow):
                write_overflow(overflow)

        total = sum([col.width for col in self.columns])

        # Resize columns if last too wide
        # TODO: Smarter column resizing, maybe pick widest column
        if (total + self.spacing * (len(self.columns) - 1)) > self.width:
            self.columns[-1].mode = Column.Grow

        for col in self.columns:
            if col.mode == Column.Grow:
                remaining = (
                    self.width - ((len(self.columns) - 1) * self.spacing) -
                    total
                )
                col.width += remaining

        if self.header:
            i = 0
            for col in self.columns:
                if i > 0:
                    fp.write(' ' * self.spacing)
                fp.write(ansi_ljust(col.text, col.width))
                i += 1

            fp.write('\n')
            fp.write('=' * self.width)
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

        :param file fp: the output file stream (usually sys.stdout or
            sys.stderr)
        :param list args: the column values for the row
        '''
        for (width, value) in zip(self.widths, args):
            fp.write(ansi_ljust(value, width))

        fp.write('\n')

    def add_cell(self, fp, col):
        '''
        Add a single cell to the table. The current row is printed if the
        column completes the row.
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
