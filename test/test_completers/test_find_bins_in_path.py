from unittest.mock import patch
import os
from pypsi.os import find_bins_in_path


class TestPathCompleter:

    def setup(self):
        base_path = os.path.dirname(os.path.abspath(__file__))
        self.actual_path = os.environ.get('PATH', '')

        self.environ_patch = patch('os.environ')
        self.environ_mock = self.environ_patch.start()

    def teardown(self):
        self.environ_mock.stop()

    def test_path_unset(self):
        # An empty or missing PATH will result in checking `./`, which checks the current repo
        self.environ_mock.return_value = f"./"
        baseline_ans = find_bins_in_path()

        self.environ_mock.return_value = None
        ans = find_bins_in_path()
        # if path is unset for some reason,
        # we should still return zero results
        assert ans == baseline_ans

    def test_path_set_empty(self):
        # An empty or missing PATH will result in checking `./`, which checks the current repo
        self.environ_mock.return_value = f"./"
        baseline_ans = find_bins_in_path()

        self.environ_mock.return_value = ""
        ans = find_bins_in_path()
        # a path of nothing should still return an empty set
        assert ans == baseline_ans

    def test_path_contains_nonexistent_path(self):
        self.environ_mock.return_value = f"{self.actual_path}"
        baseline_ans = find_bins_in_path()

        self.environ_mock.return_value = f"{self.actual_path}:nonexistent"
        ans = find_bins_in_path()

        # a path variable with a non-existent directory should still return some bins
        # this isn't a great test, because baseline_ans could still return an empty set
        assert ans == baseline_ans
