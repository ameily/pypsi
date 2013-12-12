

class Plugin(object):
    pass


class InputPreprocessor(object):
    pass


class Command(object):

    def __init__(self, name, usage=None, category=None):
        self.name = name
        self.usage = usage
        self.category = category

    def run(self, shell, ctx):
        raise NotImplementedError()

