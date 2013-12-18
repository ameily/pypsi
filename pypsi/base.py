
import argparse


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

    def error(self, shell, msg):
        shell.error(self.name, ": ", msg, '\n')

    def run(self, shell, args, ctx):
        raise NotImplementedError()

    def setup(self, shell):
        return 0


class PypsiArgParser(argparse.ArgumentParser):

    def __init__(self, *args, **kwargs):
        kwargs['add_help'] = False
        super(PypsiArgParser, self).__init__(*args, **kwargs)
        self.add_argument(
            '-h', '--help', help='print this help message', action='store_true'
        )
        self.last_error = None

    def parse_args(self, *args, **kwargs):
        self.last_error = None
        return super(PypsiArgParser, self).parse_args(*args, **kwargs)

    def error(self, message):
        self.last_error = message
