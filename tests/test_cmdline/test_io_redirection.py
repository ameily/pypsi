

from pypsi.cmdline import *
from nose.tools import *
import os
import stat
import tempfile


class TestIoRedirection(object):

    def setUp(self):
        self.remove = []

    def tearDown(self):
        for path in self.remove:
            os.remove(path)

    def mktempfile(self, data=None):
        fd, path = tempfile.mkstemp()
        if data:
            os.write(fd, data)
        os.close(fd)

        self.remove.append(path)

        return path

    def test_output_nomode_path(self):
        path = self.mktempfile(b"hello")
        ci = CommandInvocation(name="echo")
        fp = ci.get_output(path)
        assert_equal(fp.name, path)
        fp.close()

    def test_output_nomode_content(self):
        path = self.mktempfile(b"hello")
        ci = CommandInvocation(name="echo")
        fp = ci.get_output(path)
        fp.write("goodbye")
        fp.close()

        fp = open(path, 'r')
        assert_equal(fp.read(), "goodbye")
        fp.close()

    def test_output_tuple_path(self):
        path = self.mktempfile(b"hello")
        output = path, 'w'
        ci = CommandInvocation(name="echo")
        fp = ci.get_output(output)
        assert_equal(fp.name, path)
        fp.close()

    def test_output_tuple_content(self):
        path = self.mktempfile(b'hello')
        output = path, 'a'
        ci = CommandInvocation(name="echo")
        fp = ci.get_output(output)
        fp.write("goodbye")
        fp.close()

        fp = open(path, 'r')
        assert_equal(fp.read(), "hellogoodbye")
        fp.close()

    def test_output_stream(self):
        path = self.mktempfile()
        fp = open(path, 'r')
        ci = CommandInvocation(name='echo')
        assert_equal(ci.get_output(fp), fp)

    def test_input_path(self):
        path = self.mktempfile(b'hello')
        ci = CommandInvocation(name='echo')
        fp = ci.get_input(path)
        assert_equal(fp.name, path)

    def test_input_content(self):
        path = self.mktempfile(b'hello')
        ci = CommandInvocation(name='echo')
        fp = ci.get_input(path)
        assert_equal(fp.read(), 'hello')
        fp.close()

    def test_input_stream(self):
        path = self.mktempfile()
        fp = open(path, 'r')
        ci = CommandInvocation(name='echo')
        assert_equal(ci.get_input(fp), fp)

    def test_input_file_not_found(self):
        path = "|file|does|not|exist"
        ci = CommandInvocation(name='echo')
        assert_raises(IORedirectionError, ci.get_input, path)

    def test_output_permission_denied(self):
        path = self.mktempfile()
        os.chmod(path, stat.S_IREAD)
        ci = CommandInvocation(name='echo')
        assert_raises(IORedirectionError, ci.get_output, path)
        os.chmod(path, stat.S_IREAD | stat.S_IWRITE)
