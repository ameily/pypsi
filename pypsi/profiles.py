#
# Copyright (c) 2016, Adam Meily <meily.adam@gmail.com>
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


class ShellProfile:

    def __init__(self, multiline: bool = False, escape_char: str = '\\',
                 case_sensitive: bool = True, eof_is_sigint: bool = False,
                 preserve_quotes: bool = False):
        # pylint: disable=too-many-arguments
        self.multiline = multiline
        self.case_sensitive = case_sensitive
        self.escape_char = escape_char
        self.eof_is_sigint = eof_is_sigint
        self.preserve_quotes = preserve_quotes


class BashProfile(ShellProfile):

    def __init__(self, **kwargs):
        kwargs.setdefault('multiline', True)
        kwargs.setdefault('escape_char', '\\')
        kwargs.setdefault('case_sensitive', True)
        super().__init__(kwargs)


class PowerShellProfile(ShellProfile):

    def __init__(self, **kwargs):
        kwargs.setdefault('multiline', True)
        kwargs.setdefault('escape_char', '`')
        kwargs.setdefault('case_sensitive', False)
        super().__init__(**kwargs)


class TabCompletionProfile(ShellProfile):

    def __init__(self, profile: ShellProfile, **kwargs):
        kwargs.setdefault('multiline', False)
        kwargs.setdefault('escape_char', profile.escape_char)
        kwargs.setdefault('case_sensitive', profile.case_sensitive)
        super().__init__(**kwargs)
