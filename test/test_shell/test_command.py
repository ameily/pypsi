import pytest
from pypsi.shell import Shell
from pypsi.core import Command



class PypsiTestException(Exception):
    pass


class PypsiTestCommand(Command):

    def __init__(self):
        super(PypsiTestCommand, self).__init__(name='test')
        self.run_hit = self.setup_hit = False
        self.args = None

    def setup(self, shell):
        self.setup_hit = True

    def run(self, shell, args):
        self.run_hit = True
        self.args = list(args)
        if args and args[0] == 'KeyboardInterrupt':
            raise KeyboardInterrupt()
        elif args and args[0] == 'PypsiTestException':
            raise PypsiTestException()

        return 0

    def reset(self):
        self.run_hit = self.setup_hit = False
        self.args = None


class PypsiTestShell(Shell):
    test_cmd = PypsiTestCommand()

    def __init__(self):
        super(PypsiTestShell, self).__init__()
        self.error_hit = False

    def error(self, *args, **kwargs):
        self.error_hit = True


class TestShellCommand(object):

    def setup(self):
        self.shell = PypsiTestShell()

    def teardown(self):
        self.shell.test_cmd.reset()
        self.shell.restore()

    def test_setup(self):
        assert self.shell.test_cmd.setup_hit is True

    def test_execute_no_args(self):
        self.shell.execute("test")
        assert self.shell.test_cmd.args == []
        assert self.shell.test_cmd.run_hit is True

    def test_execute_args(self):
        self.shell.execute("test -x -y 'hello world'")
        assert self.shell.test_cmd.run_hit is True
        assert self.shell.test_cmd.args == ['-x', '-y', 'hello world']

    def test_command_not_found(self):
        self.shell.execute("asdf")
        assert self.shell.error_hit is True

    def test_syntax_error(self):
        self.shell.execute("test > <")
        assert self.shell.error_hit is True
        assert self.shell.test_cmd.run_hit is False

    def test_sigint(self):
        with pytest.raises(KeyboardInterrupt):
            self.shell.execute("test KeyboardInterrupt")

    def test_unhandled_exception(self):
        with pytest.raises(PypsiTestException):
            self.shell.execute('test PypsiTestException')
