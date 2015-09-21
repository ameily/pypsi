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


def safe_open(path, mode='r', chunk_size=4096, ascii_is_utf8=True,
              errors='ignore'):
    '''
    Retrieves a file's encoding and returns the opened file. If the opened file
    begins with a BOM (Byte Order Mark), it is read before the file object is
    returned. This allows callers to not have to handle BOMs of files.

    :param str path: file path to open
    :param str mode: the mode to open the file (see :func:`open`)
    :param int chunk_size: number of bytes to read to determine encoding
    :param bool ascii_is_utf8: whether to force UTF-8 encoding if the file is \
        dected as ASCII
    :param str errors: determines how errors are handled and is passed to \
        the call to :func:`open`.
    :returns file: the opened file object
    '''

    if 'b' in mode:
        return open(path, mode)

    first = None
    with open(path, 'rb') as fp:
        bin = first = fp.read(chunk_size)
        result = chardet.detect(bin)

    if not first:
        return open(path, mode)

    enc = result['encoding']
    if ascii_is_utf8 and enc == 'ascii':
        enc = 'utf-8'

    fp = codecs.open(path, mode, encoding=enc, errors=errors)
    for bom in (codecs.BOM_UTF32_BE, codecs.BOM_UTF32_LE, codecs.BOM_UTF8,
                codecs.BOM_UTF16_BE, codecs.BOM_UTF16_LE):
        if first.startswith(bom):
            fp.seek(len(bom))
            break

    return fp


def safe_open_fp(fp, mode='r', chunk_size=4096, ascii_is_utf8=True,
                 errors='ignore'):
    '''
    Retrieves a file's encoding from an open file. If the file
    begins with a BOM (Byte Order Mark), it is read before the file object is
    returned. This allows callers to not have to handle BOMs of files.

    :param str fp: opened file to determine encoding
    :param int chunk_size: number of bytes to read to determine encoding
    :param bool ascii_is_utf8: whether to force UTF-8 encoding if the file is \
        dected as ASCII
    :param str errors: determines how errors are handled and is passed to \
        the call to :func:`open`.
    :returns file: the opened file object
    '''

    first = None
    bin = first = fp.read(chunk_size)
    fp.seek(0)
    result = chardet.detect(bin)
    if not first:
        return fp

    enc = result['encoding']
    if ascii_is_utf8 and enc == 'ascii':
        enc = 'utf-8'

    buffer = io.BufferedReader(fp)
    new_fp = io.TextIOWrapper(buffer, encoding=enc, errors=errors)
    for bom in (codecs.BOM_UTF32_BE, codecs.BOM_UTF32_LE, codecs.BOM_UTF8,
                codecs.BOM_UTF16_BE, codecs.BOM_UTF16_LE):
        if first.startswith(bom):
            new_fp.seek(len(bom))
            break

    return new_fp
