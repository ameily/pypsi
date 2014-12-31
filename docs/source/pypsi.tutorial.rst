Pypsi Shell and Command API
===========================

This guide will walk through the API and design of Pypsi commands and plugins.

Pypsi Command API
-----------------

All Pypsi commands will inherit from the base command class:
:class:`pypsi.base.Command`. Each command has several attributes that determines
how the command is added to the shell. These are:

 * ``name`` - the command name that the user will type. Commands may contain
   letters, numbers, underscores, and dashes.
 * ``brief`` - a short description of what the command does.
 * ``usage`` - the usage message displayed when the user requests help.
 * ``topic`` - the topic ID used to categorize the command. This is useful when
   the user lists all available commands. The shell will attempt to categorize
   commands under headings. Al builtin commands have, by default, their topic
   set to ``"shell"``.

To ensure that commands are pluggable, commands should accept all of these
attribtues in their constructor so that a shell may customize the command when
loading. However, this is not a requirement. All builtin commands
accept all of the attribute in their constructor.

The command hook :meth:`~pypsi.base.Command.setup` is called once the command
has been created and added to the shell. The setup hook is where setup and
initialization code will reside. Commands should not hold any configuration or
state information in the command itself. However, use the
:attr:`~pypsi.Shell.ctx` to hold stateful information. Storing information in
the shell's context is done for two reasons:

 * The shell's state is stored in a single place. This allows for easy and
   uniform serialization and deserialization to enable persistent shell
   sessions.
 * Multiple instances of a shell can contain share the same command instance.

When a command is executed by the user, the command's
:meth:`~pypsi.base.Command.run` function is called.

Accepting Arguments
~~~~~~~~~~~~~~~~~~~


Printing
~~~~~~~~

Colors
""""""

Errors
""""""


Pypsi Plugins API
-----------------

Plugins extend the shell through the use of several hooks.