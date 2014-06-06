

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
            start = end+1
        else:
            line_end = None
            for i in range(end, start-1, -1):
                if text[i].isspace():
                    line_end = i
                    break
            line = text[start:line_end]
            start = line_end+1

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


def obj_str(obj, max_children=3):
    if isinstance(obj, bool):
        return "bool( {} )".format(obj)
    elif isinstance(obj, int):
        return "int( {:d} )".format(obj)
    elif isinstance(obj, float):
        return "float( {:g} )".format(obj)
    elif isinstance(obj, (list, tuple)):
        if max_children > 0 and len(obj) > max_children:
            obj = [o for o in obj[:max_children]]
            obj.append('...')

        return "list( {} )".format(
            ', '.join([obj_str(child, max_children=max_children) for child in obj])
        )
    elif obj == None:
        return '<null>'
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
                    overflow[column_idx] = value[col.width:]
                    fp.write(value[:col.width])
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
