
import sys
from pypsi.pipes import ThreadLocalStream
from pypsi.shell import Shell
from pypsi.core import pypsi_print
from nose.tools import *



class PypsiTestShell(Shell):
    pass


class TestShellBootstrap(object):

    def setUp(self):
        self.real_stdout = sys.stdout
        self.real_stderr = sys.stderr
        self.real_stdin = sys.stdin
        self.real_print = print
        self.shell = PypsiTestShell()

    def tearDown(self):
        self.shell.restore()

    def test_bootstrap_streams(self):
        for attr in ('stdout', 'stderr', 'stdin'):
            yield self._test_bootstrap_stream_type, attr
            yield self._test_bootstrap_stream_instance, attr

    def _test_bootstrap_stream_type(self, attr):
        assert_is_instance(getattr(sys, attr), ThreadLocalStream)

    def _test_bootstrap_stream_instance(self, attr):
        assert_equal(
            getattr(sys, attr)._get_target_stream(),
            getattr(self, 'real_' + attr)
        )

    def test_bootstrap_print(self):
        assert_equal(print, pypsi_print)

    def test_restore_print(self):
        self.shell.restore()
        assert_equal(print, self.real_print)

    def test_restore_streams(self):
        for attr in ('stdout', 'stderr', 'stdin'):
            yield self._test_restore_stream_type, attr
            yield self._test_restore_stream_instance, attr

    def _test_restore_stream_type(self, attr):
        self.shell.restore()
        assert_not_is_instance(getattr(sys, attr), ThreadLocalStream)

    def _test_restore_stream_instance(self, attr):
        self.shell.restore()
        assert_equal(
            getattr(sys, attr),
            getattr(self, 'real_'+attr)
        )
