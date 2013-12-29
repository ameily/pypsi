
class PypsiStream(object):

    def __init__(self, fobj, prefix='', postfix=''):
        self.fobj = fobj
        self.prefix = prefix
        self.postfix = postfix

    def __call__(self, *args):
        return self.write(*args)

    def write(self, *args):
        if self.prefix:
            self.fobj.write(self.prefix)

        for s in args:
            if isinstance(s, str):
                self.fobj.write(s)
            else:
                self.fobj.write(str(s))

        if self.postfix:
            self.fobj.write(self.postfix)
