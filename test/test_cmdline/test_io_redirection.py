
import pytest
from pypsi.cmdline import *
import os
import stat
import tempfile


class TestIoRedirection(object):

    def setup(self):
        self.remove = []

    def tearDown(self):
        for path in self.remove:
            os.chmod(path, stat.S_IREAD | stat.S_IWRITE)
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
        assert fp.name == path
        fp.close()

    def test_output_nomode_content(self):
        path = self.mktempfile(b"hello")
        ci = CommandInvocation(name="echo")
        fp = ci.get_output(path)
        fp.write("goodbye")
        fp.close()

        fp = open(path, 'r')
        assert fp.read() == "goodbye"
        fp.close()

    def test_output_tuple_path(self):
        path = self.mktempfile(b"hello")
        output = path, 'w'
        ci = CommandInvocation(name="echo")
        fp = ci.get_output(output)
        assert fp.name == path
        fp.close()

    def test_output_tuple_content(self):
        path = self.mktempfile(b'hello')
        output = path, 'a'
        ci = CommandInvocation(name="echo")
        fp = ci.get_output(output)
        fp.write("goodbye")
        fp.close()

        fp = open(path, 'r')
        assert fp.read() == "hellogoodbye"
        fp.close()

    def test_output_stream(self):
        path = self.mktempfile()
        fp = open(path, 'r')
        ci = CommandInvocation(name='echo')
        assert ci.get_output(fp) == fp

    def test_input_path(self):
        path = self.mktempfile(b'hello')
        ci = CommandInvocation(name='echo')
        fp = ci.get_input(path)
        assert fp.name == path

    def test_input_content(self):
        path = self.mktempfile(b'hello')
        ci = CommandInvocation(name='echo')
        fp = ci.get_input(path)
        assert fp.read() == 'hello'
        fp.close()

    def test_input_stream(self):
        path = self.mktempfile()
        fp = open(path, 'r')
        ci = CommandInvocation(name='echo')
        assert ci.get_input(fp) == fp

    def test_input_file_not_found(self):
        path = "|file|does|not|exist"
        ci = CommandInvocation(name='echo')
        with pytest.raises(IORedirectionError):
            ci.get_input(path)

    def test_output_permission_denied(self):
        path = self.mktempfile()
        os.chmod(path, stat.S_IREAD)
        ci = CommandInvocation(name='echo')
        with pytest.raises(IORedirectionError):
            ci.get_output(path)

