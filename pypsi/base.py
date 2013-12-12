

class Plugin(object):
    pass


class Preprocessor(object):
    pass


class Command(object):

    def __init__(self, name, usage=None, category=None, pipe='str'):
        self.name = name
        self.usage = usage
        self.category = category
        self.pipe = pipe

    def run(self, shell, args, ctx):
        raise NotImplementedError()

    def setup(self, shell):
        return 0

