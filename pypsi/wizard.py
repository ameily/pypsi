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

import os
import readline
import netaddr
import re
from pypsi.cmdline import StatementParser, StringToken
from pypsi.stream import AnsiCodes
from pypsi.format import title_str
from pypsi.namespace import Namespace


def required_validator(ns, value):
    if value is None:
        raise ValueError("Value is required")


    if not isinstance(value, str):
        return value

    value = value.strip()
    if not value:
        raise ValueError("Value is required")
    return value


def int_validator(min=None, max=None):
    def validator(ns, value):
        if not value:
            return value

        value = int(value)
        if max is not None and value > max:
            raise ValueError("Value must be less than " + str(max))
        if min is not None and value < min:
            raise ValueError("Value must be greater than " + str(min))
        return value
    return validator


def file_validator(ns, value):
    if value and (not os.path.exists(value) or not os.path.isfile(value)):
        raise ValueError("File does not exist")
    return value


def directory_validator(ns, value):
    if value and (not os.path.exists(value) or not os.path.isdir(value)):
        raise ValueError("Directory does not exist")
    return value


def hostname_or_ip_validator(ns, value):
    if value is None:
        return value

    value = value.strip()
    if not value:
        return value

    if value[0].isdigit():
        try:
            ip = netaddr.IPAddress(value)
        except:
            raise ValueError("Invalid IP address")
    else:
        hostname_re = re.compile(r'^[a-zA-Z0-9.\-]+$')
        if not re.match(r'^[a-zA-Z0-9.\-]+$', value):
            raise ValueError("Invalid hostname")
    return value


def module_name_validator(type_str):
    def validator(ns, value):
        if not isinstance(value, str):
            return value

        value = value.strip()
        if not value:
            return value

        if not re.match(r'^(?:[a-zA-Z]+)(?:\.[a-zA-Z]+)*', value):
            raise ValueError("Invalid "+type_str)
        return value
    return validator


def package_name_validator(type_str):
    def validator(ns, value):
        if not isinstance(value, str):
            return value

        value = value.strip()
        if not value:
            return value

        if not re.match(r'^[a-zA-Z][a-zA-Z0-9_]+$', value):
            raise ValueError("Invalid "+type_str)

        return value
    return validator

def choice_validator(choices):
    def validator(ns, value):
        if not isinstance(value, str):
            return value

        value = value.strip()
        if not value:
            return value

        if value not in choices:
            raise ValueError('Invalid choice')

        return value
    return validator

def boolean_validator(ns, value):
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        t = value.lower()
        if t in ('true', 't', '1', 'y', 'yes'):
            return True
        elif t in ('false', 'f', '0', 'n', 'no'):
            return False
    raise ValueError("Value is not true or false")

def lowercase_validator(ns, value):
    return value.lower() if value else ''



class WizardStep(object):

    def __init__(self, id, name, help, default=None, completer=None, validators=None):
        self.id = id
        self.name = name
        self.help = help
        self.default = default
        self.completer = completer
        if isinstance(validators, (list, tuple)):
            self.validators = validators
        elif validators:
            self.validators = [validators]
        else:
            self.validators = []

    def validate(self, ns, value):
        if self.validators:
            v = value
            for c in self.validators:
                v = c(ns, v)
            return v
        return value

    def complete(self, wizard, args, prefix):
        return self.completer(wizard, args, prefix) if self.completer else []


class PromptWizard(object):

    def __init__(self, name, description, steps=None):
        self.name = name
        self.description = description
        self.steps = steps
        self.values = Namespace()
        self.parser = StatementParser()

    def run(self, shell):
        self.old_completer = readline.get_completer()
        readline.set_completer(self.complete)
        print(
            title_str("Entering " + self.name + " Wizard", width=shell.width, box=True, align='center'),
            '\n',
            self.description, '\n\n',
            "To exit, enter either Ctrl+C, Ctrl+D, or 'quit'. For help "
            "about the current step, enter 'help' or '?'.",
            sep=''
        )

        running = True
        for step in self.steps:
            self.active_step = step
            valid = False
            while not valid:
                raw = None
                prompt = step.name
                if step.default is not None:
                    d = step.default
                    if callable(d):
                        d = d(self.values)
                    prompt += ' [{}]'.format(d)
                prompt += ': '
                try:
                    raw = input(prompt)
                except (KeyboardInterrupt, EOFError):
                    print()
                    print(AnsiCodes.red, "Wizard canceled", AnsiCodes.reset, sep='')
                    readline.set_completer(self.old_completer)
                    return None

                if raw.lower() == 'quit':
                    print(AnsiCodes.red, "Exiting wizard", AnsiCodes.reset, sep='')
                    readline.set_completer(self.old_completer)
                    return None
                elif raw.lower() in ('?', 'help'):
                    print(step.help)
                else:
                    if not raw.strip() and step.default is not None:
                        raw = step.default

                    try:
                        value = step.validate(self.values, raw)
                    except ValueError as e:
                        print(AnsiCodes.red, "Error: ", str(e), AnsiCodes.reset, sep='')
                        print(AnsiCodes.yellow, step.name, ": ", step.help, sep='')
                    else:
                        self.values[step.id] = value
                        valid = True

        readline.set_completer(self.old_completer)
        return self.values

    def complete(self, text, state):
        if state == 0:
            begidx = readline.get_begidx()
            endidx = readline.get_endidx()
            line = readline.get_line_buffer()
            prefix = line[begidx:endidx] if line else ''

            line = line[:endidx]
            tokens = self.parser.tokenize(line)
            tokens = self.parser.condense(tokens)
            args = [t.text for t in tokens if isinstance(t, StringToken)]
            self.completions = self.active_step.complete(self, args, prefix)
        return self.completions[state] if state < len(self.completions) else None


