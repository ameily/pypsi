from unittest.mock import patch

from pypsi.os import find_bins_in_path


# Example Data
DIR1 = ['cat', 'grep', 'find', 'sort']
DIR2 = ['awk', 'sed', 'ed', 'tr']


class TestPathCompleter:

    def setup(self):
        self.listdir_patch = patch('os.listdir')
        self.listdir_mock = self.listdir_patch.start()

        self.isfile_patch = patch('os.path.isfile')
        self.isfile_mock = self.isfile_patch.start()

        self.access_patch = patch('os.access')
        self.access_mock = self.access_patch.start()

        # Always pretend files are real and executable
        self.isfile_patch.return_value = True
        self.access_patch.return_value = True

    def teardown(self):
        self.listdir_mock.stop()
        self.isfile_mock.stop()
        self.access_mock.stop()

    def test_path_contains_nonexistent_path(self):
        self.listdir_mock.side_effect = [DIR1, FileNotFoundError, DIR2]
        ans = find_bins_in_path()

        bins = set()
        bins.update(DIR1)
        bins.update(DIR2)
        assert ans == bins

    def test_permission_denied(self):
        self.listdir_mock.side_effect = [DIR1, PermissionError, DIR2]
        ans = find_bins_in_path()

        bins = set()
        bins.update(DIR1)
        bins.update(DIR2)
        assert ans == bins
