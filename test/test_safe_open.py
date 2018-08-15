
import tempfile
import os
import codecs
import pytest
from pypsi.utils import safe_open

TEXT = """Lorem ipsum dolor sit amet, consectetur adipiscing elit.
Duis vestibulum urna lacus, nec dictum tortor auctor at. Donec eu ligula eget
nisl sagittis suscipit eu sed nisl. Vestibulum blandit fermentum velit vel
lobortis. Quisque sodales aliquam est, non ornare urna tincidunt pretium.
Morbi sed elit pharetra, gravida orci pulvinar, blandit nulla. Proin eget
blandit lacus. Donec nec arcu nibh. Suspendisse vulputate sodales neque non
pretium. Morbi aliquam consequat tristique. Fusce odio lacus, vulputate vitae
porttitor quis, condimentum sit amet elit."""


class SafeOpenTestCase:

    def setup(self):
        self.remove = []

    def teardown(self):
        for path in self.remove:
            os.remove(path)

    def mktempfile(self, data):
        fd, path = tempfile.mkstemp()
        os.write(fd, data)
        os.close(fd)

        self.remove.append(path)

        return path

    def _test_path_and_fileobj(self, data, expected, **kwargs):
        # write the file to disk
        path = self.mktempfile(data)

        path_fp = safe_open(path, 'r', **kwargs)
        path_data = path_fp.read()
        path_fp.close()

        fp_fp = safe_open(open(path, 'rb'), 'r', **kwargs)
        fp_data = fp_fp.read()
        fp_fp.close()

        assert path_data == fp_data
        assert path_data == expected

    def test_ascii(self):
        self._test_path_and_fileobj(
            TEXT.encode('ascii'), TEXT
        )

    def test_utf8(self):
        self._test_path_and_fileobj(
            codecs.BOM_UTF8 + TEXT.encode('utf-8'), TEXT
        )

    def test_utf16(self):
        self._test_path_and_fileobj(
            codecs.BOM_UTF16_BE + TEXT.encode('utf-16-be'), TEXT
        )
        self._test_path_and_fileobj(
            codecs.BOM_UTF16_LE + TEXT.encode('utf-16-le'), TEXT
        )

    def test_utf32(self):
        self._test_path_and_fileobj(
            codecs.BOM_UTF32_BE + TEXT.encode('utf-32-be'), TEXT
        )
        self._test_path_and_fileobj(
            codecs.BOM_UTF32_LE + TEXT.encode('utf-32-le'), TEXT
        )

    def test_invalid_ascii(self):
        path = self.mktempfile(b'hello\xC3\x93')
        fp = safe_open(path, 'r', ascii_is_utf8=False, chunk_size=5)
        with pytest.raises(UnicodeDecodeError):
            fp.read()

    def test_rb_path(self):
        path = self.mktempfile(b"hello")
        fp = safe_open(path, 'rb')
        assert fp.mode == 'rb'

    def test_rb_fp(self):
        path = self.mktempfile(b"hello")
        fp = open(path, 'rb')
        assert fp == safe_open(fp, 'rb')

    def test_empty_file_path(self):
        path = self.mktempfile(b'')
        assert safe_open(path, 'r').mode == 'r'

    def test_empty_file_fp(self):
        path = self.mktempfile(b'')
        fp = open(path, 'rb')
        assert fp == safe_open(fp, 'r')
