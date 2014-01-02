
import argparse


class Plugin(object):

    def __init__(self, preprocess=None, postprocess=None):
        self.preprocess = preprocess
        self.postprocess = postprocess

    def setup(self, shell):
        return 0

    def on_input(self, shell, line):
        return line

    def on_tokenize(self, shell, tokens, origin):
        return tokens

    def on_input_canceled(self, shell):
        return 0

    def on_statement_finished(self, shell):
        return 0


class Command(object):

    def __init__(self, name, usage=None, brief=None, topic=None, pipe='str'):
        self.name = name
        self.usage = usage or ''
        self.brief = brief or ''
        self.topic = topic or 'misc'
        self.pipe = pipe or 'str'

    def complete(self, shell, args, prefix):
        return []

    def usage_error(self, shell, *args):
        shell.error(self.name, ": ", *args)
        shell.error('\n')
        shell.warn(self.usage, '\n')

    def error(self, shell, *args):
        shell.error(self.name, ": ", *args)

    def run(self, shell, args, ctx):
        raise NotImplementedError()

    def setup(self, shell):
        return 0

    def fallback(self, *args):
        return None



class PrintHelpMessage(Exception):

    def __init__(self, message):
        self.message = message


class ArgumentError(Exception):

    def __init__(self, message):
        self.message = message


class PypsiArgParser(argparse.ArgumentParser):

    def __init__(self, *args, **kwargs):
        super(PypsiArgParser, self).__init__(*args, **kwargs)

    def parse_args(self, shell, *args, **kwargs):
        self.rc = None
        self.help_msg = None
        try:
            return super(PypsiArgParser, self).parse_args(*args, **kwargs)
        except PrintHelpMessage as e:
            shell.warn(e.message)
            self.rc = 0
        except ArgumentError as e:
            self.rc = 1
            shell.error(e.message, '\n')
            shell.warn(self.format_help())
        return None

    def error(self, message):
        raise ArgumentError(message)

    def exit(self, status=0, message=None):
        raise PrintHelpMessage(self.help_msg)

    def _print_message(self, msg, file=None):
        self.help_msg = msg
