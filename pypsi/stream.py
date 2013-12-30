
class PypsiStream(object):

    def __init__(self, fobj, prefix='', postfix=''):
        self.fobj = fobj
        self.prefix = prefix
        self.postfix = postfix

    def __call__(self, *args):
        return self.write(*args)

    def write(self, *args):
        stream = self.fobj if not callable(self.fobj) else self.fobj()
        if self.prefix:
            stream.write(self.prefix)

        for s in args:
            if isinstance(s, str):
                stream.write(s)
            elif s is not None:
                stream.write(str(s))

        if self.postfix:
            stream.write(self.postfix)
