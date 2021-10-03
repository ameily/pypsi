
import sys
import pytest
from pypsi.proxy import ThreadLocalProxy
from pypsi.shell import Shell
from pypsi.ansi import pypsi_print



class PypsiTestShell(Shell):
    pass


class TestShellBootstrap(object):

    def setup(self):
        self.real_stdout = sys.stdout
        self.real_stderr = sys.stderr
        self.real_stdin = sys.stdin
        self.real_print = print
        self.shell = None

    def teardown(self):
        if self.shell:
            self.shell.restore()

    @pytest.mark.parametrize('attr', ('stdout', 'stderr', 'stdin'))
    def test_bootstrap_stream_type(self, attr):
        self.shell = PypsiTestShell()
        assert isinstance(getattr(sys, attr), ThreadLocalProxy)

    @pytest.mark.parametrize('attr', ('stdout', 'stderr', 'stdin'))
    def test_bootstrap_stream_instance(self, attr):
        self.shell = PypsiTestShell()
        assert getattr(sys, attr)._get_target() == getattr(self, 'real_' + attr)

    def test_bootstrap_print(self):
        self.shell = PypsiTestShell()
        assert print is pypsi_print

    def test_restore_print(self):
        self.shell = PypsiTestShell()
        self.shell.restore()
        assert print is self.real_print

    @pytest.mark.parametrize('attr', ('stdout', 'stderr', 'stdin'))
    def test_restore_stream_type(self, attr):
        self.shell = PypsiTestShell()
        self.shell.restore()
        assert not isinstance(getattr(sys, attr), ThreadLocalProxy)

    @pytest.mark.parametrize('attr', ('stdout', 'stderr', 'stdin'))
    def test_restore_stream_instance(self, attr):
        self.shell = PypsiTestShell()
        self.shell.restore()
        assert getattr(sys, attr) is getattr(self, 'real_'+attr)
