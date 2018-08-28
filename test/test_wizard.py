import os
import pytest
from pypsi import wizard as wiz
from pypsi.namespace import Namespace


class TestWizard:

    def test_required_validator_empty_str(self):
        with pytest.raises(ValueError):
            wiz.required_validator(Namespace(), '')

    def test_required_validator_valid(self):
        assert wiz.required_validator(Namespace(), 'hello') == 'hello'

    def test_required_validator_nonstring(self):
        assert wiz.required_validator(Namespace(), 10) == 10

    def test_required_validator_none(self):
        with pytest.raises(ValueError):
            wiz.required_validator(Namespace(), None)

    def test_int_validator_plain_valid(self):
        validator = wiz.int_validator()
        assert validator(Namespace(), '10') == 10

    def test_int_validator_min(self):
        validator = wiz.int_validator(min=11)
        with pytest.raises(ValueError):
            validator(Namespace(), '10')

    def test_int_validator_max(self):
        validator = wiz.int_validator(max=11)
        with pytest.raises(ValueError):
            validator(Namespace(), '15')

    def test_int_validator_range(self):
        validator = wiz.int_validator(min=10, max=20)
        assert validator(Namespace(), '15') == 15

    def test_int_validator_none(self):
        validator = wiz.int_validator()
        assert validator(Namespace(), None) is None

    def test_file_validator_file(self):
        assert wiz.file_validator(Namespace(), __file__) == __file__

    def test_file_validator_directory(self):
        with pytest.raises(ValueError):
            wiz.file_validator(Namespace(), "." + os.path.sep)

    def test_directory_validator_directory(self):
        assert wiz.directory_validator(Namespace(), "." + os.path.sep) == "." + os.path.sep

    def test_directory_validator_file(self):
        with pytest.raises(ValueError):
            wiz.directory_validator(Namespace(), __file__)

    def test_hostname_validator_valid(self):
        assert wiz.hostname_or_ip_validator(Namespace(), 'google.com') == 'google.com'

    def test_ip_validator_valid(self):
        assert wiz.hostname_or_ip_validator(Namespace(), '192.168.0.1') == '192.168.0.1'

    def test_ip_validator_invalid(self):
        with pytest.raises(ValueError):
            wiz.hostname_or_ip_validator(Namespace(), '0asdf')

    def test_hostname_validator_invalid(self):
        with pytest.raises(ValueError):
            wiz.hostname_or_ip_validator(Namespace(), 'asdf\x1b')
