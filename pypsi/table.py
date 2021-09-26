
import os
import sys
from typing import List, TextIO
from .ansi import ansi_align, ansi_len, wrap, ansi_title


def _build_row(row: List[str], sep: str, column_widths: List[int]) -> str:
    '''
    Convert a table row to a word-wrapped string.

    :param row: the table row
    :param sep: the horizontal seperator between cells
    :param column_widths: the width, in characters, of each column
    :return: the word-wrapped table row
    '''
    # Word wrap each column. This creates a list of lines in each column
    columns = [list(wrap(col, width)) for col, width in zip(row, column_widths)]
    line_count = max(len(col) for col in columns)
    for column, width in zip(columns, column_widths):
        if len(column) < line_count:
            # extend the column with empty strings to make handle cell overflow
            column.extend([''] * (line_count - len(column)))

        for i in range(len(column)):
            column[i] = ansi_align(column[i].strip(), 'left', width)


    lines = (sep.join(col[i] for col in columns) for i in range(line_count))

    return os.linesep.join(lines)


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

    def append(self, *row):
        '''
        Add a row to the table.

        :param list args: the column values
        '''
        if len(row) != self.columns:
            raise TypeError(f'incorrect number of columns in row: received {len(row)}, expected '
                            f'{self.columns}')

        self.rows.append([str(col) for col in row])
        self.column_widths = [max(item, ansi_len(col))
                              for item, col in zip(self.column_widths, self.rows[-1])]

        return self

    def extend(self, *rows):
        '''
        Add multiple rows to the table, each argument should be a list of
        column values.
        '''
        for row in rows:
            self.append(*row)
        return self

    def resize(self) -> None:
        '''
        Resize the column sizes based on content.
        '''
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

    def write(self, file: TextIO = None):
        '''
        Print the table to a specified file stream.

        :param file file: output stream
        '''
        file = file or sys.stdout.thread_local_get()
        self.resize()
        sep = ' ' * self.spacing
        rows = iter(self.rows)

        if self.header:
            line = _build_row(next(rows), sep, self.column_widths)
            print(ansi_title(line), word_wrap=False, file=file)

        for row in rows:
            print(_build_row(row, sep, self.column_widths), word_wrap=False, file=file)


class FixedColumnTable(object):
    '''
    A table that has preset column widths.
    '''

    def __init__(self, widths: List[int], spacing: int = 1, file: TextIO = None,
                 header: bool = True):
        '''
        :param list widths: the list of column widths (`int`)
        '''
        self.widths = widths
        self.spacing = spacing
        self.file = file or sys.stdout.thread_local_get()
        self.columns = len(widths)
        self.header = header

    def append(self, *row) -> None:
        if len(row) != self.columns:
            raise TypeError(f'incorrect number of columns in row: received {len(row)}, expected '
                            f'{self.columns}')

        padding = ' ' * self.spacing
        line = _build_row(row, padding, self.widths)
        if self.header:
            line = ansi_title(line)
            self.header = False

        print(line, word_wrap=False, file=self.file)
        return self

    def extend(self, *rows) -> None:
        for row in rows:
            self.append(*row)
        return self
