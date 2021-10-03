from unittest.mock import patch, PropertyMock
from io import StringIO
from datetime import datetime
from pypsi.plugins.variable import *
from pypsi.cmdline import StringToken, WhitespaceToken
from pypsi.shell import Shell
from pypsi.profiles import BashProfile


class PluginShell(Shell):
    plugin = VariablePlugin(locals={'local_var': 'asdf'})


class TestVariablePlugin:

    def setup(self):
        self.features = BashProfile()
        self.shell = PluginShell(profile=self.features)
        self.shell.ctx.vars['callable'] = lambda: 'callable'
        self.plugin = self.shell.plugin
        self.cmd = self.shell.commands['var']

    def teardown(self):
        self.shell.restore()

    def test_get_subtokens_none(self):
        assert list(get_subtokens(StringToken(0, 'hello, adam'), '$', self.features)) == [StringToken(0, 'hello, adam')]

    def test_get_subtokens_single(self):
        assert (
            list(get_subtokens(StringToken(0, 'hello, $name, welcome'), '$', self.features)) ==
            [StringToken(0, 'hello, '), VariableToken(0, '$', 'name'), StringToken(1, ', welcome')]
        )

    def test_get_subtokens_multi(self):
        assert (
            list(get_subtokens(StringToken(0, '$name, welcome to $city'), '$', self.features)) ==
            [VariableToken(0, '$', 'name'), StringToken(1, ', welcome to '), VariableToken(0, '$', 'city')]
        )

    def test_get_subtokens_escape(self):
        assert (
            list(get_subtokens(StringToken(0, 'hello, \\$name'), '$', self.features)) ==
            [StringToken(0, 'hello, $name')]
        )

    def test_get_subtokens_dbl_escape(self):
        assert (
            list(get_subtokens(StringToken(0, 'hello, \\\\$name'), '$', self.features)) ==
            [StringToken(0, 'hello, \\\\'), VariableToken(0, '$', 'name')]
        )

    def test_get_subtokens_repeat(self):
        assert (
            list(get_subtokens(StringToken(0, 'hello $name$name'), '$', self.features)) ==
            [StringToken(0, 'hello '), VariableToken(0, '$', 'name'), VariableToken(0, '$', 'name')]
        )

    def test_get_subtokens_var_escape_next(self):
        assert (
            list(get_subtokens(StringToken(0, 'hello $name\\n'), '$', self.features)) ==
            [StringToken(0, 'hello '), VariableToken(0, '$', 'name'), StringToken(0, '\\n')]
        )

    def test_expand_str(self):
        self.shell.ctx.vars['test_var'] = 'hello'
        assert self.plugin.expand(self.shell, VariableToken(0, '$', 'test_var')) == 'hello'

    def test_expand_empty(self):
        assert self.plugin.expand(self.shell, VariableToken(0, '$', 'does_not_exist')) == ''

    def test_expand_callable(self):
        assert self.plugin.expand(self.shell, VariableToken(0, '$', 'callable')) == 'callable'

    def test_expand_managed_var(self):
        self.shell.ctx.vars['test_var'] = 'message'
        var = ManagedVariable(lambda shell2: shell2.ctx.vars['test_var'])
        self.shell.ctx.vars['managed'] = var
        assert self.plugin.expand(self.shell, VariableToken(0, '$', 'managed')) == 'message'

    def test_var_token_eq_none(self):
        assert VariableToken(0, '$', 'name') != None

    def test_on_tokenize(self):
        self.shell.ctx.vars['token'] = 'first_token'
        self.shell.ctx.vars['message'] = 'second_message'
        assert self.plugin.on_tokenize(
            self.shell,
            [StringToken(0, 'first $token'), WhitespaceToken(1), StringToken(2, 'second $message')],
            'input'
        ) == [StringToken(0, 'first '), StringToken(1, 'first_token', quote='"'), WhitespaceToken(2),
              StringToken(3, 'second '), StringToken(4, 'second_message', quote='"')]

    def test_safe_date_format_valid(self):
        dt = datetime(2008, 12, 6, 5, 45, 0)
        assert safe_date_format('%c', dt) == dt.strftime('%c')

    def test_safe_date_format_invalid(self):
        # Behavior of strftime changed between Python 3.3 and 3.7.
        assert safe_date_format('%q', datetime.now()) in ('<invalid date time format>', '%q')

    def test_environ_vars(self):
        assert self.shell.ctx.vars['PATH'] != ''

    def test_local_var(self):
        assert self.shell.ctx.vars['local_var'] == 'asdf'

    def test_set_prompt(self):
        PROMPT = 'new_prompt> '
        self.plugin.set_prompt(self.shell, PROMPT)
        assert self.shell.prompt == PROMPT

    @patch('sys.stdout', new_callable=StringIO)
    def test_cmd_list(self, stdout):
        rc = self.cmd.run(self.shell, ['--list'])
        val = stdout.getvalue()

        assert rc == 0
        assert 'local_var' in val

    @patch('sys.stdout', new_callable=StringIO)
    def test_cmd_delete_success(self, stdout):
        self.shell.ctx.vars['del_me'] = 'delete me'
        rc = self.cmd.run(self.shell, ['--delete', 'del_me'])
        assert rc == 0
        assert 'del_me' not in self.shell.ctx.vars

    def test_cmd_delete_managed(self):
        rc = self.cmd.run(self.shell, ['--delete', 'date'])
        assert rc == -1
        assert 'date' in self.shell.ctx.vars

    @patch('sys.stderr', new_callable=StringIO)
    def test_cmd_delete_failed(self, stderr):
        rc = self.cmd.run(self.shell, ['--delete', 'asdfasdfasdfasdf'])
        assert rc == -1
        assert len(stderr.getvalue()) > 0

    def test_cmd_set_valid(self):
        rc = self.cmd.run(self.shell, ['new_var', '=', '10'])
        assert rc == 0
        assert self.shell.ctx.vars['new_var'] == '10'

    @patch('sys.stderr', new_callable=StringIO)
    def test_cmd_set_parse_error(self, stderr):
        rc = self.cmd.run(self.shell, ['new_var = ', '10', '20 30'])
        assert rc == 1
        assert len(stderr.getvalue()) > 0

    @patch('sys.stderr', new_callable=StringIO)
    def test_cmd_set_readonly(self, stderr):
        rc = self.cmd.run(self.shell, ['date = now'])
        assert rc == -1
        assert len(stderr.getvalue()) > 0

    def test_cmd_set_prompt(self):
        PROMPT = 'new_prompt> '
        rc = self.cmd.run(self.shell, ['prompt', '=', PROMPT])
        assert rc == 0
        assert self.shell.get_current_prompt() == PROMPT

    @patch('sys.stdout', new_callable=StringIO)
    def test_cmd_print_simple(self, stdout):
        rc = self.cmd.run(self.shell, ['local_var'])
        assert rc == 0
        assert 'asdf' in stdout.getvalue()

    @patch('sys.stdout', new_callable=StringIO)
    def test_cmd_print_callable(self, stdout):
        rc = self.cmd.run(self.shell, ['callable'])
        assert rc == 0
        assert 'callable' in stdout.getvalue()

    @patch('sys.stdout', new_callable=StringIO)
    def test_cmd_print_prompt(self, stdout):
        rc = self.cmd.run(self.shell, ['prompt'])
        assert rc == 0
        assert self.shell.get_current_prompt() in stdout.getvalue()

    @patch('sys.stderr', new_callable=StringIO)
    def test_cmd_print_invalid(self, stderr):
        rc = self.cmd.run(self.shell, ['asdfasdfasdf'])
        assert rc == 1
        assert len(stderr.getvalue()) > 0

    @patch('sys.stderr', new_callable=StringIO)
    def test_cmd_print_invalid2(self, stderr):
        rc = self.cmd.run(self.shell, ['asdf', 'asdf', 'asdf'])
        assert rc == 1
        assert len(stderr.getvalue()) > 0

    @patch('sys.stderr', new_callable=StringIO)
    def test_cmd_invalid(self, stderr):
        rc = self.cmd.run(self.shell, [])
        assert rc ==1
        assert len(stderr.getvalue()) > 0

    @patch('sys.stderr', new_callable=StringIO)
    def test_cmd_invalid_args(self, stderr):
        rc = self.cmd.run(self.shell, ['--bad-arg'])
        assert rc == 1
        assert len(stderr.getvalue()) > 0

    @patch('sys.stderr', new_callable=StringIO)
    def test_cmd_help(self, stderr):
        rc = self.cmd.run(self.shell, ['--help'])
        assert rc == 0
        assert len(stderr.getvalue()) > 0


