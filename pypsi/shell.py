
from pypsi.base import Plugin, Command, Preprocessor
from pypsi.cmdline import StatementParser, StatementSyntaxError, StatementContext
from pypsi.namespace import Namespace
from pypsi.stream import PypsiStream
import readline
import sys


class Shell(object):

    def __init__(self, shell_name='pypsi', exit_rc=-1024):
        self.real_stdout = sys.stdout
        self.real_stdin = sys.stdin
        self.real_stderr = sys.stderr

        self.shell_name = shell_name
        self.exit_rc = exit_rc
        self.commands = {}
        self.preprocessors = []
        self.plugins = []
        self.prompt = "{name} )> ".format(name=shell_name)
        self.features = Namespace('globals')

        self.streams = { }
        self.add_stream('error', PypsiStream(sys.stderr))
        self.add_stream('warn', PypsiStream(sys.stderr))
        self.add_stream('info', PypsiStream(sys.stdout))

        self.parser = StatementParser()
        self.register_base_plugins()

    def add_stream(self, name, stream):
        self.streams[name] = stream
        setattr(self, name, stream)

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
        self.plugins.append(plugin)
        if isinstance(plugin, Command):
            self.commands[plugin.name] = plugin

        if isinstance(plugin, Preprocessor):
            self.preprocessors.append(plugin)

        plugin.setup(self)
        return 0

    def get_plugin(self, search):
        for plugin in self.plugins:
            if isinstance(plugin, search):
                return plugin
        return None

    def cmdloop(self):
        rc = 0
        while rc != self.exit_rc:
            try:
                raw = raw_input(self.prompt)
                rc = self.execute(raw)
            except EOFError:
                rc = self.exit_rc
                print "exiting...."
            except KeyboardInterrupt:
                print
                for pp in self.preprocessors:
                    pp.on_input_canceled(self)
        return rc

    def execute(self, raw, ctx=None):
        if not ctx:
            ctx = StatementContext()

        for pp in self.preprocessors:
            raw = pp.on_input(self, raw)
            if not raw:
                return 0

        tokens = self.parser.tokenize(raw)
        statement = None
        for pp in self.preprocessors:
            tokens = pp.on_tokenize(self, tokens)
            if not tokens:
                break

        if not tokens:
            return 0

        try:
            statement = self.parser.build(tokens, ctx)
        except StatementSyntaxError as e:
            self.error(self.shell_name, ": ", str(e), '\n')
            return 1

        rc = None
        if statement:
            (params, op) = statement.next()
            while params:
                if params.name not in self.commands:
                    statement.ctx.reset_io()
                    self.error(self.shell_name, ": ", params.name, ": command not found\n")
                    return 1

                cmd = self.commands[params.name]

                statement.ctx.setup_io(cmd, params, op)
                rc = self.run_cmd(cmd, params, statement.ctx)
                if op == '||':
                    if rc == 0:
                        statement.ctx.reset_io()
                        return 0
                elif op == '&&' or op == '|':
                    if rc != 0:
                        statement.ctx.reset_io()
                        return rc

                (params, op) = statement.next()

        statement.ctx.reset_io()

        return rc

    def run_cmd(self, cmd, params, ctx):
        rc = cmd.run(self, params.args, ctx)
        if rc > 0:
            self.warn(cmd.usage)
        return rc

