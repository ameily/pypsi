
from pypsi.base import Plugin, Command, InputPreprocessor
from pypsi.cmdline import StatementParser, StatementSyntaxError
import readline


class Shell(object):

    def __init__(self, shell_name='pypsi', exit_rc=-1024):
        self.shell_name = shell_name
        self.exit_rc = 1024
        self.commands = {}
        self.plugins = {}
        self.prompt = "{name} )> ".format(name=shell_name)

        self.parser = StatementParser(True)
        self.register_base_plugins()

    def register_base_plugins(self):
        cls = self.__class__
        for name in dir(cls):
            attr = getattr(cls, name)
            if isinstance(attr, Command) or isinstance(attr, Plugin):
                self.register(attr)
            '''
            elif callable(attr) and name.startswith("do_"):
                usage = ''
                cmd_name = name[3:]
                if hasattr(cls, 'help_'+cmd_name):
                    usage = getattr(cls, 'help_'+cmd_name)
                else:
                    usage = attr.__doc__

                wrapper = FunctionCommandWrapper(name[3:], attr, usage)
                self.register(wrapper)
            '''

    def register(self, plugin):
        if isinstance(plugin, Command):
            self.commands[plugin.name] = plugin

        plugin.setup(self)
        return 0

    def cmdloop(self):
        rc = 0
        while rc != self.exit_rc:
            raw = raw_input(self.prompt)
            tokens = self.parser.tokenize(raw)
            if not tokens:
                continue

            try:
                statement = self.parser.build(tokens)
            except StatementSyntaxError as e:
                print "{name}: {msg}".format(name=self.shell_name, msg=str(e))


    def precmd(self, cmd):
        pass

    def postcmd(self, cmd):
        pass

    def onecmd(self, raw):
        '''
        tokens = self.parser.tokenize(raw)
        for pp in self.preprocessors:
            pp.on_tokenize(self, tokens)
            if not tokens:
                break

        if not tokens:
            return 0

        cmdline = self.parser.build(tokens)
        for pp in self.preprocessors:
            pp.on_cmdline_built(cmdline)

        if not cmdline:
            return 0

        for cmd in cmdline:
            self.run(cmd)
        '''
        pass
