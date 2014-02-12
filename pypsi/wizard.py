
import os
import readline
import netaddr
from pypsi.cmdline import StatementParser, StringToken
from pypsi.stream import AnsiStdout
from pypsi.format import word_wrap, title_str
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
        raise Value("Directory does not exist")
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


def paackage_name_validator(type_str):
    def validator(ns, value):
        if not isinstance(value, str):
            return value

        value = value.strip()
        if not value:
            return value

        if not re.match(r'^[a-zA-Z][a-zA-Z0-9_]+$'):
            raise ValueError("Invalid "+type_str)

        return value
    return validator



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
        print(
            title_str("Entering " + self.name + " Wizard", width=shell.width, box=True, align='center'),
            '\n',
            self.description, '\n\n',
            word_wrap(
                "To exit, enter either Ctrl+C, Ctrl+D, or 'quit'. For help "
                "about the current step, enter 'help' or '?'.", shell.width
            ),
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
                    print(AnsiStdout.red, "Wizard canceled", AnsiStdout.reset, sep='')
                    return None

                if raw.lower() == 'quit':
                    print(AnsiStdout.red, "Exiting wizard", AnsiStdout.reset, sep='')
                    return None
                elif raw.lower() in ('?', 'help'):
                    print(word_wrap(step.help, shell.width))
                else:
                    if not raw and step.default is not None:
                        raw = step.default

                    try:
                        value = step.validate(self.values, raw)
                    except ValueError as e:
                        print(AnsiStdout.red, "Error: ", str(e), AnsiStdout.reset, sep='')
                        print(AnsiStdout.yellow, step.name, ": ", step.help, sep='')
                    else:
                        self.values[step.id] = value
                        valid = True

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



def test():
    shell = Namespace(width=80)
    ns = PromptWizard(
        name="Datastore Configuration",
        description="Setup Metasponse Datastore",
        steps=(
            WizardStep('host', 'Hostname', '', 'localhost', validators=required_validator),
            WizardStep('port', "Port", '', 3306, validators=(required_validator, int_validator(0, 0xffff)))
        )
    ).run(shell)

    print(ns.host)
    print(ns.port)

