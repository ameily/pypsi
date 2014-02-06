
def highlight(target, term, color='1;32'):
    if not color:
        return target

    s = target.lower()
    t = term.lower()
    print("term:", term)
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


def title_str(title, width=80, align='left', hr='='):
    lines = []
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
            self.columns = [Column("")] * columns
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
        total = sum([ col.width for col in self.columns ])
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
            i = 0
            for (col, value) in zip(self.columns, row):
                if i > 0:
                    fp.write(' ' * self.spacing)
                if isinstance(value, str):
                    pass
                else:
                    value = str(value)

                #fp.write("{{: <{}}}".format(col.width).format(value))
                fp.write(value.ljust(col.width))
                i += 1
            fp.write('\n')
        return 0


class Column(object):
    Shrink = 0
    Grow = 1

    def __init__(self, text, mode=0):
        self.text = text
        self.mode = mode
        self.width = len(text)


class FixedColumnTable(object):

    def __init__(self, widths):
        self.widths = [int(width) for width in widths]

    def write_row(self, fp, *args):
        for (width, value) in zip(self.widths, args):
            fp.write(value.ljust(width))
            #diff = width - len(value)
            #if diff > 0:
            #    fp.write(' ' * diff)
        fp.write('\n')

