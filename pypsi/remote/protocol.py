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

import json


class InvalidMessageError(Exception):
    pass


def json_assert_field(obj, name, types=None, optional=False):
    if name not in obj:
        if optional:
            return None
        else:
            raise InvalidMessageError("missing required field "+name)

    if types:
        if optional and obj[name] is None:
            return None
        elif not isinstance(obj[name], types):
            raise InvalidMessageError("invalid type for field "+name)

    return obj[name]


class CompletionRequest(object):
    status = 'pypsi.shell.complete.request'

    @classmethod
    def from_json(cls, obj):
        return cls(
            input=json_assert_field(obj, 'input', str),
            prefix=json_assert_field(obj, 'prefix', str)
        )

    def __init__(self, input, prefix):
        self.input = input
        self.prefix = prefix

    def json(self):
        return {
            'input': self.input,
            'prefix': self.prefix,
            'status': self.status
        }


class CompletionResponse(object):
    status = 'pypsi.shell.complete.response'

    @classmethod
    def from_json(cls, obj):
        return cls(json_assert_field(obj, 'completions', list))

    def __init__(self, completions):
        self.completions = completions

    def json(self):
        return {'completions': self.completions, 'status': self.status}


class InputResponse(object):
    status = 'pypsi.shell.input.response'

    @classmethod
    def from_json(cls, obj):
        return cls(
            input=json_assert_field(obj, 'input', str),
            sig=json_assert_field(obj, 'sig', str, optional=True)
        )

    def __init__(self, input, sig=None):
        self.input = input
        self.sig = sig

    def json(self):
        return {'input': self.input, 'sig': self.sig, 'status': self.status}


class InputRequest(object):
    status = 'pypsi.shell.input.request'

    @classmethod
    def from_json(cls, obj):
        return cls(json_assert_field(obj, 'prompt', str))

    def __init__(self, prompt):
        self.prompt = prompt

    def json(self):
        return {'prompt': self.prompt, 'status': self.status}


class ShellOutputResponse(object):
    status = 'pypsi.shell.output.response'

    @classmethod
    def from_json(cls, obj):
        output = json_assert_field(obj, 'output', str)
        return ShellOutputResponse(output)

    def __init__(self, output):
        self.output = output

    def json(self):
        return {'output': self.output, 'status': self.status}
