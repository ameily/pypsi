from typing import List
from .ansi import ansi_align, ansi_len, wrap


class Table:
    '''
    Variable width table.
    '''

    def __init__(self, columns: int, width: int = 80, spacing: int = 1, header: bool = True):
        '''
        :param multiple columns: a list of either class:`Column` instances or a
            single `int` defining how many columns to create
        :param int width: the maximum width of the entire table
        :param int spacing: the amount of space characters to display between
            columns
        :param bool header: whether to display header row with the column names
        '''
        self.columns = columns
        self.column_widths = [0] * columns
        self.width = width
        self.spacing = spacing
        self.header = header
        self.rows = []

    def append(self, *args):
        '''
        Add a row to the table.

        :param list args: the column values
        '''
        self.rows.append([str(item) for item in args])
        self.column_widths = [max(item, ansi_len(value))
                              for item, value in zip(self.column_widths, self.rows[-1])]

        return self

    def extend(self, *args):
        '''
        Add multiple rows to the table, each argument should be a list of
        column values.
        '''
        for row in args:
            self.append(*row)
        return self

    def resize(self) -> None:
        padding = self.spacing * (self.columns - 1)
        if (sum(self.column_widths) + padding) <= self.width:
            return

        # assume each column will have the same size
        max_column_width = (self.width - padding) /self.columns
        # determine if any column is less than the guess size
        columns_widths = [min(max_column_width, item) for item in self.column_widths]
        # determine if there is any extra space after we shurnk the table to fit contents
        extra_size = self.width - padding - sum(columns_widths)

        if extra_size:
            # there is extra space, distribute it to remaining columns, prioritizing the last column
            for i in range(self.columns - 1, -1, -1):
                if self.column_widths[i] <= max_column_width:
                    continue

                delta = self.column_widths[i] - columns_widths
                grow_size = min(extra_size, delta)
                extra_size -= grow_size
                columns_widths[i] += grow_size

                if not extra_size:
                    break

        self.column_widths = columns_widths

    def _build_row(self, row: List[str], sep: str) -> str:
        columns = [list(wrap(col, width)) for col, width in zip(row, self.column_widths)]
        line_count = max(len(col) for col in columns)
        ret = ''
        for column, width in zip(columns, self.column_widths):
            if len(column) < line_count:
                column.extend([''] * (line_count - len(column)))

            for i in range(len(column)):
                column[i] = [ansi_align(line.strip(), 'left', width) for line in column[i]]

        # TODO

    def write(self, fp):
        '''
        Print the table to a specified file stream.

        :param file fp: output stream
        '''
        self.resize()
        for row in self.rows:
            columns = [list(wrap(col, width)) for col, width in zip(row, self.column_widths)]
            line_count = max(len(col) for col in columns)
            for column in columns:
                if len(column) < line_count:
                    column.extend([''] * (line_count - len(column)))

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
    '''


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
