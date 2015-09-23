Pypsi - Python Pluggable Shell Interface
========================================

.. image:: https://coveralls.io/repos/ameily/pypsi/badge.svg?branch=master&service=github
  :target: https://coveralls.io/github/ameily/pypsi?branch=master

.. image:: https://travis-ci.org/ameily/pypsi.svg?branch=master
  :target: https://travis-ci.org/ameily/pypsi

Develop extensible and powerful command line interface shells with minimal code. Want to jump straight into the API? Take a look at :doc:`pypsi.tutorial`.

Python Pluggable Shell Interface, or pypsi, is a framework for developing
command line based shell interfaces, akin to bash or csh. It is intended to be
a replacement for the builtin Python ``cmd`` module.

Pypsi is targetted towards both rapid prototype interfaces and large stable
shells. The bootstraping code is very small with very little boilerplate. Pypsi
ships with a great deal of capabilities out of the box, all of which can be used
or ignored. Pypsi is pluggable which allows commands, features, and plugins to be
developed independently in their own source files and/or Python classes. This
results in a very clean source repository. The actual code to setup and run the
shell is exetremely small, on the order of ~20-50 lines of code.

Pypsi, at its core, is pluggable. There are many hooks that allow plugin authors
to extend and modify the core behavior of pypsi. Commands are isolated classes
that make distribution, sharing, and modification easy.

Releases
--------

The pypsi source code is hosted at `GitHub <https://github.com/ameily/pypsi>`_
and releases are stored at `PyPI <https://pypi.python.org/pypi/pypsi>`_. The
latest version can also be install via pip:

::

    $ pip install pypsi

Documentation can be found on `GitHub Pages <http://ameily.github.io/pypsi>`_.

Features
--------

The following capabilities ship with pypsi and are available out of the box.

-  I/O redirection
-  Flexible API
-  Tab completion
-  Multiplatform
-  Minimal dependencies
-  Colors
-  Session tips and message of the day (MOTD)
-  Automated help, usage messages, and argument parsing
-  Word wrapping
-  Term highlighting (grep)
-  Tables
-  Prompt wizards
-  ``cmd`` plugin to migrate existing ``cmd`` commands into pypsi

Demo
----

The ``demo.py`` source file can be run to show off some of the base commands and
features that ship with pypsi (the ``demo.py`` file can be downloaded from the
git repo at https://github.com/ameily/pypsi/blob/master/demo.py). The commands
displayed below are all optional: pypsi does not require the use of any command
or plugin. The ``demo.py`` file is meant to be a reference to the Pypsi API and
design. Use it as a starting point for your first shell.

Variables
~~~~~~~~~

::

    pypsi)> var name = "Paul"

    pypsi)> var house = "Atredis"

    pypsi)> echo My name is $name, and I belong to House $house

    My name is Paul, and I belong to House Atredis

    pypsi)> var -l

    name     Paul
    house    Atredis

    pypsi)> var -d name

    pypsi)> echo $name

    pypsi)> var name = "Paul $house"

    pypsi)> echo $name

    Paul Atredis

I/O redirection
~~~~~~~~~~~~~~~

::

    pypsi)> echo Hello

    Hello

    pypsi)> echo Hello > output.txt

    pypsi)> echo Goodbye

    pypsi)> xargs -I{} "echo line: {}" < output.txt

    line: Hello
    line: Goodbye

    pypsi)> cat output.txt | grep ll

    Hello

System commands
~~~~~~~~~~~~~~~

Allows execution of external applications. Command mimics Python's
``os.system()`` function.

::

    pypsi)> ls

    pypsi: ls: command not found

    pypsi)> system ls

    include/
    src/
    README.md

    pypsi)> system ls | system grep md

    README.md

Fallback command
~~~~~~~~~~~~~~~~

Allows the developer to set which command gets called if one does not exist in
the current shell. This is very useful, for example, if you want to fallback on
any OS installed executables. In this example, the fallback command is
``system``.

::

    pypsi)> ls

    include/
    src/
    README.md

Command chaining
~~~~~~~~~~~~~~~~

::

    pypsi)> echo Hello && echo --bad-arg && echo goodbye

    Hello
    echo: unrecgonized arguments: --bad-arg

    pypsi)> echo Hello ; echo --bad-arg ; echo goodbye

    Hello
    echo: unrecgonized arguments: --bad-arg
    goodbye

    pypsi)> echo --bad-arg || echo first failed

    echo: unrecgonized arguments: --bad-arg
    first failed

Multiline commands
~~~~~~~~~~~~~~~~~~

::

    pypsi)> echo Hello, \
    > Dave

    Hello, Dave

    pypsi)> echo This \
    > is \
    > pypsi \
    > and it rocks

    This is pypsi and it rocks

Macros
~~~~~~

Macros are analogous to functions in bash. They provide the ability to create
new commands in the shell.

::

    pypsi)> macro hello
    > echo Hello, $1
    > echo Goodbye from macro $0
    > end

    pypsi)> hello Adam

    Hello, Adam
    Goodbye from macro hello

Prompt Wizards
~~~~~~~~~~~~~~

Prompt wizards ask the user a series of questions and request input. Input is
tab completed, validated, and returned. The wizard can be used for easy
configuration of components that require a substantial amount of input.

::

    pypsi)> wizard
    +-----------------------------------------------------------------------------+
    |                    Entering Example Configuration Wizard                    |
    +-----------------------------------------------------------------------------+
    Shows various examples of wizard steps

    To exit, enter either Ctrl+C, Ctrl+D, or 'quit'. For help about the current
    step, enter 'help' or '?'.

    IP Address: <enter>

    Error: Value is required
    Local IP Address or Host name

    IP Address: 192.168.0.10

    TCP Port [1337]: <enter>

    File path: /var/lo<tab>

    local/  lock/   log/

    File path: /var/log/<tab>

    Xorg.1.log        btmp              faillog           upstart/
    Xorg.1.log.old    dist-upgrade/     fontconfig.log    wtmp
    alternatives.log  distccd.log       fsck/
    apt/              dmesg             lastlog
    bootstrap.log     dpkg.log          mongodb/

    File path: /var/log/dpkg.log

    Shell mode [local]: asdf

    Error: Invalid choice

    Mode of the shell

    Shell mode [local]: remote

    Config ID    Config Value
    ================================================================================
    ip_addr      172.16.11.204
    port         1337
    path         /var/log/dpkg.log
    mode         remote

Background
----------

I developed Pypsi while working on a commerical product with a command line
interface. Originally, we used the ``cmd`` module, which was fine when we only
had a few commands that didn't accept complex arguments. As we added more
commands and more features, maintainability and extensibility became extremely
complicated and time consuming.

I took what I had learned from the ``cmd`` module, ORM libraries such as
MongoEngine, and features from proven great command line interfaces such as Git
and then I developed Pypsi. In order for Pypsi to be viable for our project, I
knew that Pypsi had to be compatible with ``cmd``, the porting process had to
take as little time as possible, and it had to be easy to understand and
maintain.

The porting process from ``cmd`` to Pypsi for our commerical project took place
in January 2014. Since then, we've had 4 stable releases, had real world
feedback, and have successfully created many Pypsi commands and plugins with
ease.

License
-------

``pypsi`` is released under the ISC premissive license.
