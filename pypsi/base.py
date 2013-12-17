

class Plugin(object):

    def setup(self, shell):
        return 0


class Preprocessor(object):

    def on_input(self, shell, line):
        return line

    def on_tokenize(self, shell, tokens):
        return tokens

    def on_input_canceled(self, shell):
        return 0


class Command(object):

    def __init__(self, name, usage=None, category=None, pipe='str'):
        self.name = name
        self.usage = usage or ''
        self.category = category
        self.pipe = pipe

    def run(self, shell, args, ctx):
        raise NotImplementedError()

    def setup(self, shell):
        return 0

