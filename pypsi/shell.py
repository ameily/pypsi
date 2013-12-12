
from pypsi.base import Plugin, Command, InputPreprocessor
from pypsi.cmdline import StatementParser, StatementSyntaxError, StatementContext
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
            try:
                raw = raw_input(self.prompt)
                rc = self.execute(raw)
            except EOFError:
                rc = self.exit_rc
                print
        return rc

    def execute(self, raw, ctx=StatementContext()):
        tokens = self.parser.tokenize(raw)
        statement = None
        if not tokens:
            return 0

        try:
            statement = self.parser.build(tokens, ctx)
        except StatementSyntaxError as e:
            print "{name}: {msg}".format(name=self.shell_name, msg=str(e))
            return 1

        rc = None
        if statement:
            (ctx, op) = statement.next()
            while ctx:
                if ctx.name not in self.commands:
                    statement.ctx.reset_io()
                    print "{}: {}: command not found".format(self.shell_name, ctx.name)
                    return 1

                cmd = self.commands[ctx.name]

                statement.ctx.setup_io(cmd, ctx, op)
                rc = self.run_cmd(cmd, ctx)
                if op == '||':
                    if rc == 0:
                        return 0
                elif op == '&&':
                    if rc != 0:
                        return rc
                elif op == '|':
                    pass

                (ctx, op) = statement.next()

        statement.ctx.reset_io()
        print "reset IO!"
        return rc

    def run_cmd(self, cmd, ctx):
        return cmd.run(self, ctx)

