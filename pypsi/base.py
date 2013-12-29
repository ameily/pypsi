
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

    def __init__(self, name, usage=None, brief=None, topic=None, pipe='str'):
        self.name = name
        self.usage = usage or ''
        self.brief = brief or ''
        self.topic = topic or 'misc'
        self.pipe = pipe or 'str'

    def error(self, shell, *args):
        shell.error(self.name, ": ", *args)

    def run(self, shell, args, ctx):
        raise NotImplementedError()

    def setup(self, shell):
        return 0

    def fallback(self, *args):
        return None



class PrintHelpMessage(Exception):
    pass

class ArgumentError(Exception):
    pass

class PypsiArgParser(argparse.ArgumentParser):

    def __init__(self, *args, **kwargs):
        #kwargs['add_help'] = False
        super(PypsiArgParser, self).__init__(*args, **kwargs)
        #self.add_argument(
        #    '-h', '--help', help='print this help message', action=HelpAction
        #)
        self.last_error = None

    def parse_args(self, shell, *args, **kwargs):
        self.rc = None
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
        #self.last_error = message
        #raise PrintHelpMessage()
        raise ArgumentError(message)

    def exit(self, status=0, message=None):
        #print "exit:", self.help_msg
        raise PrintHelpMessage(self.help_msg)

    def _print_message(self, msg, file=None):
        self.help_msg = msg
        #print "_print_message(", self.help_msg, ")"

    #def print_help(self, file=None):
    #    self.help_msg = self.format_help()
    #    print "HELP:", self.help_msg

    #def print_usage(self, file=None):
    #    self.help_msg = self.format_usage()
    #    print "USAGE:", self.help_msg
