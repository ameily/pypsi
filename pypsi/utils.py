#
# Copyright (c) 2015, Adam Meily <meily.adam@gmail.com>
# Pypsi - https://github.com/ameily/pypsi
#
# Permission to use, copy, modify, and/or distribute this software for any
# purpose with or without fee is hereby granted, provided that the above
# copyright notice and this permission notice appear in all copies.
#
# THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
# WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
# MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
# ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
# WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
# ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
# OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
#

'''
Utility functions and classes.
'''

import chardet
import codecs
import io


def safe_open(file, mode='r', chunk_size=4096, ascii_is_utf8=True, **kwargs):
    '''
    Detect a file's encoding, skip any Byte Order Marks that the are located
    at the beginning of the file, and returns the opened file stream. The
    `file` argument can be either a string containing a path to the file or
    an already open binary file-like object.

    :param str file: path to the file or a binary file-like object
    :param str mode: the mode to open the file (see :func:`open`)
    :param int chunk_size: number of bytes to read to determine encoding
    :param bool ascii_is_utf8:
        whether to force UTF-8 encoding if the file is dected as ASCII
    :param str errors:
        determines how errors are handled and is passed to the call to
        :func:`open`.
    :returns file: the opened file stream
    '''

    is_path = isinstance(file, str)
    header = None

    if 'b' in mode:
        # open the file as binary
        return open(file, mode) if is_path else file

    if is_path:
        # open the file on disk and read the first chunk
        with open(file, 'rb') as fp:
            header = fp.read(chunk_size)
    else:
        # read the header and move back to the beginning of the file
        header = file.read(chunk_size)
        file.seek(0)

    if not header:
        return open(file, mode) if is_path else file

    result = chardet.detect(header)
    enc = result['encoding']
    if ascii_is_utf8 and enc == 'ascii':
        # the encoding has been detected as ASCII, check if we should open the
        # fileas UTF-8
        enc = 'utf-8'

    if is_path:
        fp = codecs.open(file, mode, encoding=enc, **kwargs)
    else:
        fp = io.TextIOWrapper(file, encoding=enc, **kwargs)

    for bom in (codecs.BOM_UTF32_BE, codecs.BOM_UTF32_LE, codecs.BOM_UTF8,
                codecs.BOM_UTF16_BE, codecs.BOM_UTF16_LE):
        if header.startswith(bom):
            fp.seek(len(bom))
            break

    return fp


def escape_string(s, escape_char, chars=' \n\t\xa0', escape_escape_char=True):
    ret = ''
    if escape_escape_char:
        escape = chars + escape_char
    else:
        escape = chars

    for c in s:
        if c in escape:
            ret += escape_char + c
        else:
            ret += c
    return ret
