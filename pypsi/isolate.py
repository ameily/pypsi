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


import sys
import io


class ClosableStream(io.StringIO):

    def __init__(self, atty=True):
        super(ClosableStream, self).__init__()
        self.atty = atty

    def isatty(self):
        return self.atty

    def close(self):
        return

    def getvalue(self):
        if not hasattr(self, '_value'):
            self._value = super(ClosableStream, self).getvalue()
        return self._value


class ShellResult(object):

    def __init__(self, prompt):
        self.prompt = [prompt]
        self.output = None
        self.error = None
        self.rc = None

    def set_post_prompt(self, prompt):
        self.prompt.append(prompt)


class IsolatedShell(object):

    def __init__(self, shell, atty=True):
        self.shell = shell
        self.atty = atty

    def get_prompt(self):
        stream = ClosableStream(self.atty)
        sys.stdout._proxy(stream, width=80)
        prompt = self.shell.get_current_prompt()
        sys.stdout._unproxy()

        return prompt

    def on_cmdloop_begin(self):
        stream = ClosableStream(self.atty)
        sys.stdout._proxy(stream, width=80)
        sys.stderr._proxy(stream, width=80)

        result = ShellResult(self.shell.get_current_prompt())

        try:
            result.rc = self.shell.on_cmdloop_begin()
        except:
            result.error = sys.exc_info()
        else:
            result.output = stream.getvalue()
        finally:
            result.set_post_prompt(self.shell.get_current_prompt())
            sys.stdout._unproxy()
            sys.stderr._unproxy()

        return result

    def execute(self, command):
        stream = ClosableStream(self.atty)
        sys.stdout._proxy(stream, width=80)
        sys.stderr._proxy(stream, width=80)

        result = ShellResult(self.shell.get_current_prompt())

        try:
            result.rc = self.shell.execute(command)
        except:
            result.error = sys.exc_info()
        finally:
            result.output = stream.getvalue()
            result.set_post_prompt(self.shell.get_current_prompt())
            sys.stdout._unproxy()
            sys.stderr._unproxy()

        return result
