Overview
========================================

Python Pluggable Shell Interface, or pypsi, is a framework for developing
command line based shell interfaces, akin to bash or csh.

Pypsi was designed around the Python ``cmd`` module. The Python ``cmd`` module
is fine for small projects with a limited number of commands and features.
However, as the interface grows, maintainability and extensibility becomes
increasingly hard. Adding features such as argument parsing after a few commands
have been implemented is exectremely time consuming.

Pypsi is targetted towards both rapid prototype interfaces and large stable
shells. The bootstraping code is very small with very little boilerplate. Pypsi
ships with a great deal of capabilities box of the box, all of which can be used
or ignore. Pypsi is pluggable which allows commands, features, and plugins be
developed independently in their own source files and/or Python classes. This
results in a very clean source repository. The actual code to setup and run the
shell is exetremely small, on the order of ~20-50 lines of code.

Pypsi, at its core, is pluggable. There are many hooks that allow plugin authors
to extend and modify the core behavior of pypsi. Commands are isolated classes
that make distribution, sharing, and modifing easy.

Caveats
-------

The only major caveat when using pypsi is that it only supports Python 3. Python
3 is the future.

Releases
--------

The pypsi source code is located on `GitHub <https://github.com/ameily/pypsi>`
and on `PyPI <https://pypi.python.org/pypi/pypsi>`. The latest version can also
be install via pip:

::

    pip install pypsi


Features
--------

The following capabilities ship with pypsi and are available out of the box.

-  I/O redirection
-  String-based pipes
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
or plugin.

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


License
-------

``pypsi`` is released under the BSD 3-Clause license.
