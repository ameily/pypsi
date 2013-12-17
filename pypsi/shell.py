
from pypsi.base import Plugin, Command, Preprocessor
from pypsi.cmdline import StatementParser, StatementSyntaxError, StatementContext
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
                print
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
            print "{name}: {msg}".format(name=self.shell_name, msg=str(e))
            return 1

        rc = None
        if statement:
            (params, op) = statement.next()
            while params:
                self.real_stderr.write("while->begin()\n")
                if params.name not in self.commands:
                    statement.ctx.reset_io()
                    print "{}: {}: command not found".format(self.shell_name, params.name)
                    return 1

                cmd = self.commands[params.name]

                statement.ctx.setup_io(cmd, params, op)
                self.real_stderr.write("run_cmd( {} )\n".format(cmd.name))
                rc = self.run_cmd(cmd, params, statement.ctx)
                self.real_stderr.write("done( {} )\n".format(cmd.name))
                if op == '||':
                    if rc == 0:
                        statement.ctx.reset_io()
                        return 0
                elif op == '&&' or op == '|':
                    if rc != 0:
                        statement.ctx.reset_io()
                        return rc

                self.real_stderr.write("pre-next()\n")
                (params, op) = statement.next()
                self.real_stderr.write("post-next()\n")

        statement.ctx.reset_io()

        return rc

    def run_cmd(self, cmd, params, ctx):
        rc = cmd.run(self, params.args, ctx)
        if rc > 0:
            ctx.stderr.write(cmd.usage.format(name=cmd.name, shell=self.shell_name))
            ctx.stderr.write("\n")
        return rc

