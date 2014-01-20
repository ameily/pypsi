
Pypsi Builtin Plugins
=====================

Pypsi ships with several useful plugins that enhance the shell.

.. toctree::
    :numbered:
    :maxdepth: 2

.. automodule:: pypsi.plugins


Block Commands
--------------

.. automodule:: pypsi.plugins.block

.. autoclass:: pypsi.plugins.block.BlockPlugin
    :members:

.. autoclass:: pypsi.plugins.block.BlockCommand
    :members:


Escape Sequence Processors
--------------------------

.. autoclass:: pypsi.plugins.hexcode.HexCodePlugin
    :members:

.. autoclass:: pypsi.plugins.multiline.MultilinePlugin
    :members:


Shell History
-------------

.. automodule:: pypsi.plugins.history


.. autoclass:: pypsi.plugins.history.HistoryPlugin
    :members:

.. autoclass:: pypsi.plugins.history.HistoryCommand
    :members:

.. autoclass:: pypsi.plugins.history.History
    :members:


Variables
---------

.. automodule:: pypsi.plugins.variable

.. autoclass:: pypsi.plugins.variable.VariablePlugin
    :members:

.. autoclass:: pypsi.plugins.variable.VariableCommand
    :members:

.. autoclass:: pypsi.plugins.variable.ManagedVariable
    :members:



Cmd
---

.. automodule:: pypsi.plugins.cmd

.. autoclass:: pypsi.plugins.cmd.CmdPlugin
    :members:

.. autoclass:: pypsi.plugins.cmd.CommandFunction
    :members:

.. autodata:: pypsi.plugins.cmd.CmdArgsList

.. autodata:: pypsi.plugins.cmd.CmdArgsString
