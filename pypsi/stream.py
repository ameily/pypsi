
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
            self.fobj.write(s)

        if self.postfix:
            self.fobj.write(self.postfix)
