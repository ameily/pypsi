Pypsi Shell and Command Tutorial
================================

This guide will walk through the API and design of Pypsi commands and plugins.

Command API
-----------

All Pypsi commands will inherit from the base command class:
:class:`pypsi.base.Command`. Each command has several attributes that determines
how the command is added to the shell. These are:

 * ``name`` - the command name that the user will type. Commands may contain
   letters, numbers, underscores, and dashes.
 * ``brief`` - a short description of what the command does.
 * ``usage`` - the usage message displayed when the user requests help.
 * ``topic`` - the topic ID used to categorize the command. This is useful when
   the user lists all available commands. The shell will attempt to categorize
   commands under headings. All builtin commands have, by default, their topic
   set to ``"shell"``.

To ensure that commands are pluggable, commands should accept all of these
attribtues in their constructor so that a shell may customize the command when
loading. However, this is not a requirement. All builtin commands
accept all of the attribute in their constructor.

The command hook :meth:`~pypsi.base.Command.setup` is called once the command
has been created and added to the shell. The setup hook is where setup and
initialization code will reside. Commands should not hold any configuration or
state information in the command itself. However, use the
shell's :attr:`~pypsi.Shell.ctx` attribute to hold stateful information. Storing
information in the shell's context is done for two reasons:

 * The shell's state is stored in a single place. This allows for easy and
   uniform serialization and deserialization to enable persistent shell
   sessions.
 * Multiple instances of a shell can contain share the same command instance.

When a command is executed by the user, the command's
:meth:`~pypsi.base.Command.run` function is called.

Accepting Arguments
~~~~~~~~~~~~~~~~~~~

All of Pypsi's bultin commands use a wrapped version of Python's :mod:`argparse`
module for argument parsing. The class :class:`~pypsi.base.PypsiArgParser`
wraps :class:`~argparse.ArgumentParser` to change the parser's behavior when the
user passes invalid arguments or asks for help. By default, the base
ArgumentParser will exit the entire program, which isn't ideal for Pypsi.

The only difference between the Pypsi :class:`pypsi.base.PypsiArgParser` and
:mod:`argparse.ArgumentParser` is that the former will raise a
:class:`pypsi.base.CommandShortCircuit` exception when the arguments aren't
valid or the user requests help (via ``-h`` or ``--help``.)

Printing
~~~~~~~~

Pypsi wraps the :meth:`print` function with its own
:meth:`~pypsi.stream.pypsi_print` function, which handles automatic word
wrapping and smart coloring.

Colors
""""""

Pypsi supplies color constants that can be printed to the screen. Colors will
only print if the output stream is a terminal (ie. the stream's ``isatty()``
returns :const:`True`.) This means that commands don't need to handle printing
colors and not printing colors, the :meth:`~pypsi.stream.pypsi_print` function
handles it.

Color codes are held in the :const:`~pypsi.stream.AnsiCodes` object. Using this
constant is straight forward. In this example, the text "Hello, World!" is
printed in red and then in green::

    print(AnsiCodes.red, "Hello, ", AnsiCodes.green, "World!", AnsiCodes.reset, sep='')

It is important to pass in ``sep=''`` when printing colors. Otherwise, the above
statement would add a space around each color, which will be confusing to the
user.

Errors
""""""

To ensure uniform error messages, the :meth:`~pypsi.base.Command.error` function
is provided to correctly format error messages. With color enabled, this will
print in red: ``<command_name>: error: <error_message>``.

Example
~~~~~~~

This example is the source code of the
:class:`~pypsi.commands.echo.EchoCommand`, which prints the arguments passed
into it to the screen::

    # Pypsi imports
    from pypsi.base import Command, PypsiArgParser, CommandShortCircuit
    import argparse

    # Custom usage message
    EchoCmdUsage = "%(prog)s [-n] [-h] message"


    class EchoCommand(Command):
        '''
        Prints text to the screen.
        '''

        def __init__(self, name='echo', topic='shell', brief='print a line of text', **kwargs):
            self.parser = PypsiArgParser(
                prog=name,
                description=brief,
                usage=EchoCmdUsage
            )

            subcmd = self.parser.add_argument_group(title='Stream')

            self.parser.add_argument(
                'message', help='message to print', nargs=argparse.REMAINDER,
                metavar="MESSAGE"
            )

            self.parser.add_argument(
                '-n', '--nolf', help="don't print newline character", action='store_true'
            )

            super(EchoCommand, self).__init__(
                name=name, usage=self.parser.format_help(), topic=topic,
                brief=brief, **kwargs
            )

        def run(self, shell, args, ctx):
            try:
                ns = self.parser.parse_args(args)
            except CommandShortCircuit as e:
                return e.code

            tail = '' if ns.nolf else '\n'

            print(' '.join(ns.message), sep='', end=tail)

            return 0

The echo command only accepts a single argument: ``-n|--nolf``. The command
itself mirrors a simple Python command line application. This means that porting
existing applications to Pypsi commands is extremely easy. Also, notice the
``try...except...`` around ``parser.parse_args``. This is catching the
:class:`~pypsi.base.CommandShortCircuit` exception, which in this case will be
thrown if the user enters any of the following:

 * ``-h``, ``--help`` - print usage information
 * ``-x`` - an invalid argument for the echo command


Shell API
---------

Pypsi shells are typically barebones and do not contain much. This is a similar
design to ORM libraries such as Django and MongoEngine, where the database table
(or document) just holds the list of attributes as class variables.

All shells much inherit from the base class :class:`~pypsi.shell.Shell`. Then,
add command instances. In this example, a new shell is created, given the name
"example" and the echo command is added, but renamed to ``print``::

    # Pypsi Imports
    from pypsi.shell import Shell
    from pypsi.commands.echo import EchoCommand

    class MyShell(Shell):
        echo_cmd = EchoCommand(name='print')

    shell = MyShell(name='example')
    shell.cmdloop()

Once running, the user will be presented with a prompt and will be able to use
the ``print`` command (which is the :class:`~pypsi.commands.echo.EchoCommand`.)

Several hooks exist in the shell that can be overriden. These include:

 * :meth:`~pypsi.shell.Shell.on_shell_ready` - called when the shell is created
 * :meth:`~pypsi.shell.Shell.on_cmdloop_begin` - called when the
   :meth:`~pypsi.shell.Shell.cmdloop` function is called
 * :meth:`~pypsi.shell.Shell.on_cmdloop_end` - called when the cmdloop has ended
   (usually because the user is exiting the shell)
