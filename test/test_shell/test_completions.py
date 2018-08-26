from unittest.mock import patch
import os
import pytest
from pypsi.shell import Shell
from pypsi.core import Command


class PypsiTestCommand(Command):
    CHOICES = ['run', 'me', 'now']

    def run(self, shell, args):
        return 0

    def complete(self, shell, token, prefix):
        return [choice for choice in self.CHOICES if not prefix or choice.startswith(prefix)]


class PypsiTestShell(Shell):
    test_cmd = PypsiTestCommand(name='test')
    test2_cmd = PypsiTestCommand(name='test-me')


class TestCompletions:

    def setup(self):
        self.shell = PypsiTestShell()

    def teardown(self):
        self.shell.restore()

    def test_clean_completions_multi_no_quote(self):
        assert self.shell._clean_completions(['file1\0', 'dir1/'], '') == ['file1', 'dir1/']

    def test_clean_completions_multi_quote(self):
        assert self.shell._clean_completions(['file1\0', 'dir1/'], '"') == ['file1', 'dir1/']

    def test_clean_completions_single_no_quote(self):
        assert self.shell._clean_completions(['file1\0'], '') == ['file1 ']

    def test_clean_completions_single_quote(self):
        assert self.shell._clean_completions(['file1\0'], '"') == ['file1" ']

    def test_clean_completions_single_escape_quote(self):
        assert self.shell._clean_completions(['"file1"\0'], '"') == ['\\"file1\\"" ']

    def test_clean_completions_single_space_no_quote(self):
        assert self.shell._clean_completions(['file 1'], '') == ['file\\ 1']

    def test_clean_completions_single_space_quote(self):
        assert self.shell._clean_completions(['file 1'], '"') == ['file 1']

    def test_command_completions_multi(self):
        print(self.shell.commands)
        assert self.shell.get_command_name_completions('te') == ['test', 'test-me']

    def test_command_completions_empty(self):
        assert self.shell.get_command_name_completions('') == ['test', 'test-me']

    def test_command_completions_no_match(self):
        assert self.shell.get_command_name_completions('ze') == []

    def test_command_completions_single(self):
        assert self.shell.get_command_name_completions('test-') == ['test-me']

    def test_get_completions_command(self):
        assert self.shell.get_completions('tes', 'tes') == ['test', 'test-me']

    def test_get_completions_chain_command(self):
        assert self.shell.get_completions('a_command && tes', 'tes') == ['test', 'test-me']

    @patch('pypsi.shell.path_completer')
    def test_get_completions_io_redirect(self, path_completer_mock):
        path_completer_mock.return_value = ['file1', 'dir1']
        assert self.shell.get_completions('test > ', '') == ['file1', 'dir1']

    @patch('pypsi.shell.path_completer')
    def test_get_completions_io_redirect_space_escape(self, path_completer_mock):
        path_completer_mock.return_value = ['file', 'dir']
        assert self.shell.get_completions('test > a_\\ ', '') == ['file', 'dir']
        path_completer_mock.assert_called_with('a_ ', '')

    @patch('pypsi.shell.path_completer')
    def test_get_completions_path_prefix(self, path_completer_mock):
        path_completer_mock.return_value = ['file', 'dir']
        assert self.shell.get_completions(os.path.sep, '') == ['file', 'dir']
        path_completer_mock.assert_called_with(os.path.sep, '')

    def test_get_completions_test_cmd(self):
        assert self.shell.get_completions('test ', '') == PypsiTestCommand.CHOICES
