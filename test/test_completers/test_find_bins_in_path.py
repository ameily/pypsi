import os
import sys
from unittest.mock import patch

from pypsi.os import find_bins_in_path


# Example Data
DIR1 = ['cat', 'grep', 'find', 'sort']
DIR2 = ['awk', 'sed', 'ed', 'tr']

if sys.platform == "win32":
    RET_DIR1 = [item + ".exe" for item in DIR1]
    RET_DIR2 = [item + ".bat" for item in DIR2]
    PATH = "asdf;qwer"
else:
    RET_DIR1 = list(DIR1)
    RET_DIR2 = list(DIR2)
    PATH = "asdf:qwer"


class TestPathCompleter:

    @patch.object(os, 'listdir', side_effect=[RET_DIR1, FileNotFoundError, RET_DIR2])
    @patch.object(os.path, 'isfile', return_value=True)
    @patch.object(os, 'access', return_value=True)
    @patch.object(os.environ, 'get', return_value=PATH)
    def test_path_contains_nonexistent_path(self, *args):
        ans = find_bins_in_path()

        bins = set()
        bins.update(DIR1)
        bins.update(DIR2)
        assert ans == bins

    @patch.object(os, 'listdir', side_effect=[RET_DIR1, PermissionError, RET_DIR2])
    @patch.object(os.path, 'isfile', return_value=True)
    @patch.object(os, 'access', return_value=True)
    @patch.object(os.environ, 'get', return_value=PATH)
    def test_permission_denied(self, *args):
        ans = find_bins_in_path()

        bins = set()
        bins.update(DIR1)
        bins.update(DIR2)
        assert ans == bins
