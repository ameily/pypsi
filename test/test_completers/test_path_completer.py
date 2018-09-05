from unittest.mock import patch
import os
import pytest
from pypsi.completers import path_completer


class TestPathCompleter:

    def setup(self):
        self.listdir_patch = patch('os.listdir')
        self.isdir_patch = patch('os.path.isdir')
        self.exists_patch = patch('os.path.exists')
        self.listdir_mock = self.listdir_patch.start()
        self.isdir_mock = self.isdir_patch.start()
        self.exists_mock = self.exists_patch.start()

    def teardown(self):
        self.listdir_patch.stop()
        self.isdir_patch.stop()
        self.exists_patch.stop()

    def test_simple_multi(self):
        self.listdir_mock.return_value = ['file1', 'file2', 'f_dir1', 'test1']
        self.isdir_mock.side_effect = [True, False, False, True, False]
        self.exists_mock.return_value = True

        ans = path_completer(os.path.join('dir', 'f'), 'f')
        assert ans == ['file1\0', 'file2\0', 'f_dir1' + os.path.sep]

    def test_empty_token(self):
        self.listdir_mock.return_value = ['file1', 'dir1']
        self.isdir_mock.side_effect = [True, False, True]
        self.exists_mock.return_value = True
        assert path_completer('', '') == ['file1\0', 'dir1' + os.path.sep]

    def test_no_matches(self):
        self.listdir_mock.return_value = ['file', 'dir']
        self.isdir_mock.side_effect = [True, False, True]
        self.exists_mock.return_value = True

        ans = path_completer(os.path.join('dir', 'fz'), 'fz')
        assert ans == []

    def test_no_exists(self):
        self.listdir_mock.return_value = []
        self.isdir_mock.return_value = False
        self.exists_mock.return_value = False
        assert path_completer(os.path.join('dir', 'f'), 'f') == []

    def test_dir_and_file(self):
        self.listdir_mock.return_value = ['dir', 'dir_file']
        self.isdir_mock.side_effect = [True, True, False]
        self.exists_mock.return_value = True
        assert path_completer('dir', 'dir') == ['dir' + os.path.sep, 'dir_file\0']

    def test_space_prefix(self):
        self.listdir_mock.return_value = ['a file', 'a dir', 'not a file']
        self.isdir_mock.side_effect = [True, False, True, False]
        self.exists_mock.return_value = True
        assert path_completer('a', 'a') == ['a file\0', 'a dir' + os.path.sep]

    def test_space_no_prefix(self):
        self.listdir_mock.return_value = ['a file', 'a dir', 'not a file']
        self.isdir_mock.side_effect = [True, False, True, False]
        self.exists_mock.return_value = True
        assert path_completer('a ', '') == ['file\0', 'dir' + os.path.sep]

    def test_path_sep_token(self):
        self.listdir_mock.return_value = ['file1', 'dir1']
        self.isdir_mock.side_effect = [True, False, True]
        self.exists_mock.return_value = True
        assert path_completer('dir' + os.path.sep, '') == ['file1\0', 'dir1' + os.path.sep]

    def test_cwd_not_dir(self):
        self.listdir_mock.return_value = ['file1']
        self.isdir_mock.side_effect = [False]
        self.exists_mock.return_value = True
        assert path_completer('f', 'f') == []

    def test_cwd_not_exist(self):
        self.listdir_mock.return_value = ['file1']
        self.isdir_mock.side_effect = [True]
        self.exists_mock.return_value = False
        assert path_completer('f', 'f') == []
