from io import StringIO
from unittest.mock import patch
from pypsi.shell import Shell
from pypsi.commands.macro import MacroCommand, Macro
from pypsi.plugins.variable import VariablePlugin

class CmdShell(Shell):
    cmd = MacroCommand(macros={'test': ['echo hello']})
    macro = Macro(['echo hello'], name='test')
    variable = VariablePlugin()


class TestMacro:

    def setup(self):
        self.shell = CmdShell()
        self.cmd = self.shell.commands['macro']
        self.macro = self.shell.commands['test']

    def teardown(self):
        self.macro.remove_var_args(self.shell)
        self.shell.restore()

    def test_add_var_args(self):
        self.macro.add_var_args(self.shell, ['arg1', 'arg2', 'arg3'])
        assert self.shell.ctx.vars['0'] == 'test'
        assert self.shell.ctx.vars['1'] == 'arg1'
        assert self.shell.ctx.vars['2'] == 'arg2'
        assert self.shell.ctx.vars['3'] == 'arg3'

    def test_remove_var_args(self):
        self.shell.ctx.vars['0'] = 'test'
        self.shell.ctx.vars['1'] = 'arg1'
        self.macro.remove_var_args(self.shell)

        assert '0' not in self.shell.ctx.vars
        assert '1' not in self.shell.ctx.vars

    @patch('test.test_commands.test_macro.CmdShell.execute')
    def test_macro_run(self, exec_mock):
        exec_mock.return_value = 0
        rc = self.macro.run(self.shell, [])
        assert rc == 0
        exec_mock.assert_called_with('echo hello')

    @patch('sys.stderr', new_callable=StringIO)
    def test_cmd_help(self, stderr):
        rc = self.cmd.run(self.shell, ['--help'])
        assert rc == 0
        assert len(stderr.getvalue()) > 0

    @patch('sys.stderr', new_callable=StringIO)
    def test_cmd_invalid_multi1(self, stderr):
        rc = self.cmd.run(self.shell, ['--show', 'asdf', '--list'])
        print(stderr.getvalue())
        assert rc == -1
        assert len(stderr.getvalue()) > 0

    @patch('sys.stderr', new_callable=StringIO)
    def test_cmd_invalid_multi2(self, stderr):
        rc = self.cmd.run(self.shell, ['--show', 'qwer', '--delete', 'qwer'])
        assert rc == -1
        assert len(stderr.getvalue()) > 0

    @patch('sys.stderr', new_callable=StringIO)
    def test_cmd_invalid_multi3(self, stderr):
        rc = self.cmd.run(self.shell, ['--delete', 'qwer', '--list'])
        assert rc == -1
        assert len(stderr.getvalue()) > 0

    @patch('sys.stdout', new_callable=StringIO)
    def test_cmd_show_exists(self, stdout):
        rc = self.cmd.run(self.shell, ['--show', 'test'])
        print(stdout.getvalue())
        assert rc == 0
        assert 'echo hello' in stdout.getvalue()

    @patch('sys.stderr', new_callable=StringIO)
    def test_cmd_show_not_exists(self, stderr):
        rc = self.cmd.run(self.shell, ['--show', 'qwer'])
        assert rc == -1
        assert len(stderr.getvalue()) > 0

    def test_cmd_delete_exists(self):
        self.shell.commands['del_me'] = 10
        self.shell.ctx.macros['del_me'] = []
        rc = self.cmd.run(self.shell, ['--delete', 'del_me'])
        assert rc == 0
        assert 'del_me' not in self.shell.commands
        assert 'del_me' not in self.shell.ctx.macros

    @patch('sys.stderr', new_callable=StringIO)
    def test_cmd_delete_not_exists(self, stderr):
        self.shell.commands['del_me'] = 10
        rc = self.cmd.run(self.shell, ['--delete', 'del_me'])
        assert rc == -1
        assert 'del_me' in self.shell.commands
        assert len(stderr.getvalue()) > 0
