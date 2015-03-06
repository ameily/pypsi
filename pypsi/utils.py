#
# Copyright (c) 2014, Adam Meily
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without modification,
# are permitted provided that the following conditions are met:
#
# * Redistributions of source code must retain the above copyright notice, this
#   list of conditions and the following disclaimer.
#
# * Redistributions in binary form must reproduce the above copyright notice, this
#   list of conditions and the following disclaimer in the documentation and/or
#   other materials provided with the distribution.
#
# * Neither the name of the {organization} nor the names of its
#   contributors may be used to endorse or promote products derived from
#   this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR
# ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON
# ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#

'''
Utility functions and classes.
'''

import chardet
import codecs


def safe_open(path, mode='r', chunk_size=4096, ascii_is_utf8=True, errors='ignore'):
    '''
    Retrieves a file's encoding and returns the opened file. If the opened file
    begins with a BOM, it is read before the file object is returned. This
    allows callers to not have to handle BOMs of files.

    :param str path: file path to open
    :param str mode: the mode to open the file (see :func:`open`)
    :param int chunk_size: number of bytes to read to determine encoding
    :param bool ascii_is_utf8: whether to force UTF-8 encoding if the file is \
        dected as ASCII
    :param str errors: determines how errors are handled and is passed to \
        the call to :func:`open`.
    :returns file: the opened file object
    '''

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
