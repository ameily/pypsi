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
Command line input wizards.
'''

import getpass
import os
import readline
import re
from pypsi.completers import path_completer
from pypsi.cmdline import StatementParser, StringToken
from pypsi.ansi import AnsiCodes
from pypsi.format import title_str
from pypsi.namespace import Namespace


HOSTNAME_RE = re.compile(r'^[a-zA-Z0-9.\-]+$')
IPV4_RE = re.compile(
    r'^[1-9](?:[0-9]{0,2})\.(?:[0-9]{1,3})\.(?:[0-9]{1,3})\.(?:[0-9]{1,3})'
    r'(?:/\d{1,2})?$'
)
MODULE_NAME_RE = re.compile(
    r'^(?:[a-zA-Z_][a-zA-Z0-9_]*)(?:\.[a-zA-Z_][a-zA-Z0-9_]*)*$'
)
PACKAGE_NAME_RE = re.compile(r'^[a-zA-Z_][a-zA-Z0-9_]+$')


def wizard_step_path_completer(shell, args, prefix):  # pylint: disable=unused-argument
    '''
    Complete a path within a wizard step. This completer will only return consistent results for
    wizards that have ``complete_single_token = True``.
    '''
    return [
        i.replace('\0', '')
        for i in path_completer(args[-1] if args else prefix, prefix)
    ]


def required_validator(ns, value):  # pylint: disable=unused-argument
    '''
    Required value wizard validator. Raises ValueError on validation error.

    :param pypsi.namespace.Namespace ns: active namespace
    :param value: input value
    :returns: validated value
    '''
    if value is None:
        raise ValueError("Value is required")

    if not isinstance(value, str):
        return value

    value = value.strip()
    if not value:
        raise ValueError("Value is required")
    return value


def int_validator(min=None, max=None):
    '''
    Integer value wizard validator creator.

    :param int min: minimum value, :const:`None` if no minimum
    :param int max: maximum value, :const:`None` if no maximum
    :returns: validator function
    '''

    def validator(ns, value):  # pylint: disable=unused-argument
        if not value:
            return value

        value = int(value)
        if max is not None and value > max:
            raise ValueError("Value must be less than " + str(max))
        if min is not None and value < min:
            raise ValueError("Value must be greater than " + str(min))
        return value
    return validator


def file_validator(ns, value):  # pylint: disable=unused-argument
    '''
    File path validator. Raises ValueError on validation error.

    :param pypsi.namespace.Namespace ns: active namespace
    :param value: input value
    :returns: validated value
    '''

    if value and (not os.path.exists(value) or not os.path.isfile(value)):
        raise ValueError("File does not exist")
    return value


def directory_validator(ns, value):  # pylint: disable=unused-argument
    '''
    Directory path validator. Raises ValueError on validation error.

    :param pypsi.namespace.Namespace ns: active namespace
    :param value: input value
    :returns: validated value
    '''

    if value and (not os.path.exists(value) or not os.path.isdir(value)):
        raise ValueError("Directory does not exist")
    return value


def hostname_or_ip_validator(ns, value):  # pylint: disable=unused-argument
    '''
    Network hostname or IPv4 address validator. Raises ValueError on validation
    error.

    :param pypsi.namespace.Namespace ns: active namespace
    :param value: input value
    :returns: validated value
    '''

    if value is None:
        return value

    value = value.strip()
    if not value:
        return value

    if value[0].isdigit():
        if not IPV4_RE.match(value):
            raise ValueError("Invalid IPv4 address")
    else:
        if not HOSTNAME_RE.match(value):
            raise ValueError("Invalid hostname")
    return value


def module_name_validator(type_str):
    '''
    Python module name validator. Raises ValueError on validation error.

    :param str type_str: the input type to reference when raising validation
     errors.
    :returns: validator function
    '''

    def validator(ns, value):  # pylint: disable=unused-argument
        if not isinstance(value, str):
            return value

        value = value.strip()
        if not value:
            return value

        if not MODULE_NAME_RE.match(value):
            raise ValueError("Invalid " + type_str)
        return value
    return validator


def package_name_validator(type_str):
    '''
    Python package name validator. Raises ValueError on validation error.

    :param str type_str: the input type to reference when raising validation
     errors.
    :returns: validator function
    '''

    def validator(ns, value):  # pylint: disable=unused-argument
        if not isinstance(value, str):
            return value

        value = value.strip()
        if not value:
            return value

        if not PACKAGE_NAME_RE.match(value):
            raise ValueError("Invalid " + type_str)

        return value
    return validator


def choice_validator(choices):
    '''
    String choice validator. Raises ValueError if input isn't a valid choice.

    :param list choices: valid choices
    :returns: validator function
    '''

    def validator(ns, value):  # pylint: disable=unused-argument
        if not isinstance(value, str):
            return value

        value = value.strip()
        if not value:
            return value

        if value not in choices:
            raise ValueError('Invalid choice')

        return value
    return validator


def boolean_validator(ns, value):  # pylint: disable=unused-argument
    '''
    Boolean validator. Raises ValueError if input isn't a boolean string.

    :param pypsi.namespace.Namespace ns: active namespace
    :param value: input value
    :returns bool: validated value
    '''
    if isinstance(value, bool):
        return value

    if isinstance(value, str):
        t = value.lower()
        if t in ('true', 't', '1', 'y', 'yes'):
            return True
        if t in ('false', 'f', '0', 'n', 'no'):
            return False

    raise ValueError("Value is not true or false")


def lowercase_validator(ns, value):  # pylint: disable=unused-argument
    '''
    Converts input string to lowercase.

    :param pypsi.namespace.Namespace ns: active namespace
    :param value: input value
    :returns: validated value (in lowercase)
    '''

    return value.lower() if value else ''


class WizardStep(object):
    '''
    A single input step in a prompt wizard.
    '''

    def __init__(self, id, name, help, default=None, completer=None,
                 validators=None, secure=False):
        '''
        :param str id: the step io, used for referencing the step's value
        :param str name: the name to display for input to the user
        :param str help: the help message to display to the user
        :param str default: the default value if the user immediately hits
            "Return"
        :param completer: a completion function
        :param validators: a single or a list of validators
        :param secure: use :meth:`~getpass.getpass` to read input from the user and hide the user's
            answer from the terminal
        '''

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
        
        self.secure = secure

    def validate(self, ns, value):
        '''
        Validate the input value. This will call the local validators
        (``self.validators``) sequentially with the following arguments:

         - ns (:class:`~pypsi.namespace.Namespace`) - the current input values
         - value - the value to validate

        Validators may change the value in place (if it is a mutable object) or
        may return the validated value that will be passed to the remaining
        validators. If a validation error occurs, raise a ValueError exception.

        :param pypsi.namespace.Namespace ns: current input values
        :param value: current input value
        :returns: validated value
        '''
        if self.validators:
            v = value
            for c in self.validators:
                v = c(ns, v)
            return v
        return value

    def complete(self, wizard, args, prefix):
        '''
        Get the list of possible completions for input. This will call the
        local completer function (``self.completer`` with the arguments:
        (``wizard``, ``args``, ``prefix``).

         - wizard (:class:`PromptWizard`) - the active wizard
         - args (``list``) - the list of input arguments
         - prefix (``str``) - the input prefix

        This function mirrors the command :meth:`~pypsi.core.Command.complete`
        function.
        '''

        return self.completer(wizard, args, prefix) if self.completer else []

    def get_input(self, prompt) -> str:
        """
        Get the input from the user.
        """
        if self.secure:
            return getpass.getpass(prompt)
        return input(prompt)


class PromptWizard(object):
    '''
    A user input prompt wizards.

    PromptWizards will walk the user through a series of questions
    (:class:`WizardStep`) and accept input. The user may at any time enter the
    ``?`` key to get help regarding the current step.

    Each step can have validators that determine if a value is valid before
    proceeding to the next step. Also, each step can have a default value that
    is saved if the user hits ``Return`` with no input.

    Once complete, the wizard will return a :class:`~pypsi.namespace.Namespace`
    object that contains all the user's answers. Each step contains an ``id``
    attribute that determines what variable is set in the returned namespace.

    For example, a step may have an id of ``"ip_addr"``. When the user enters
    ``"192.168.0.1"`` for this step, the input can be retrieved through the
    namespace's ``ip_addr`` attribute.
    '''

    def __init__(self, name, description, steps=None, features=None, complete_single_token=False):
        '''
        :param str name: the prompt wizard name to display to the user
        :param str description: a short description of what the wizard does
        :param list steps: a list of :class:`WizardStep` objects
        :param bool complete_single_token: treat tab completion requests as a literal string and
            do not tokenize the input (complete args will always be a single item list)
        '''
        self.name = name
        self.description = description
        self.steps = steps
        self.features = features
        self.complete_single_token = complete_single_token
        self.values = Namespace()
        self.completions = None
        self.old_completer = None
        self.active_step = None

    def run(self, shell, print_header=True):
        '''
        Execute the wizard, prompting the user for input.

        :param pypsi.shell.Shell shell: the active shell
        :returns: a :class:`~pypsi.namespace.Namespace` object containing all
         the answers on success, :const:`None` if the user exited the wizard
        '''

        self.old_completer = readline.get_completer()
        readline.set_completer(self.complete)

        if print_header:
            print(
                title_str("Entering " + self.name + " Wizard",
                          width=shell.width, box=True, align='center'),
                '\n',
                self.description, '\n\n',
                "To exit, enter either Ctrl+C, Ctrl+D, or 'quit'. For help "
                "about the current step, enter 'help' or '?'.", sep=''
            )

        for step in self.steps:
            self.active_step = step
            valid = False
            while not valid:
                print()
                raw = None
                prompt = step.name
                default = step.default
                if default is not None:
                    if callable(default):
                        default = default(self.values)
                    
                    if step.secure:
                        prompt += ' [{}]'.format('*' * len(default))
                    else:
                        prompt += ' [{}]'.format(default)
                
                prompt += ': '
                try:
                    raw = step.get_input(prompt)
                except (KeyboardInterrupt, EOFError):
                    print()
                    print(AnsiCodes.red, "Wizard canceled", AnsiCodes.reset,
                          sep='')
                    readline.set_completer(self.old_completer)
                    return None

                if raw.lower() == 'quit':
                    print(AnsiCodes.red, "Exiting wizard", AnsiCodes.reset,
                          sep='')
                    readline.set_completer(self.old_completer)
                    return None

                if raw.lower() in ('?', 'help'):
                    print(step.help)
                else:
                    if not raw.strip() and default is not None:
                        raw = default

                    try:
                        value = step.validate(self.values, raw)
                    except ValueError as e:
                        print(AnsiCodes.red, "Error: ", str(e),
                              AnsiCodes.reset, sep='')
                        print(AnsiCodes.yellow, step.name, ": ", step.help,
                              AnsiCodes.reset, sep='')
                    else:
                        self.values[step.id] = value
                        valid = True

        readline.set_completer(self.old_completer)
        return self.values

    def complete(self, text, state):  # pylint: disable=unused-argument
        '''
        Tab complete for the current step.
        '''

        if state == 0:
            parser = StatementParser(self.features)
            begidx = readline.get_begidx()
            endidx = readline.get_endidx()
            line = readline.get_line_buffer()
            prefix = line[begidx:endidx] if line else ''

            line = line[:endidx]
            if self.complete_single_token:
                # treat the entire line as a single token
                args = [line]
            else:
                # tokenize the line
                tokens = parser.tokenize(line)
                tokens = parser.condense(tokens)
                args = [t.text for t in tokens if isinstance(t, StringToken)]
            self.completions = self.active_step.complete(self, args, prefix)

        if state < len(self.completions):
            return self.completions[state]
        return None
