pypsi.cmdline - User input processing
=====================================

.. toctree::
    :numbered:
    :maxdepth: 2

.. automodule:: pypsi.cmdline



Commands and expressions
------------------------

.. autoclass:: Expression
    :members:

.. autoclass:: CommandParams
    :members:



Tokens
------

Constants
^^^^^^^^^

These constants are returned by each token's `add_char()` function to determine
where tokens begin, end, and what they contain.

.. autodata:: TokenContinue
.. autodata:: TokenEnd
.. autodata:: TokenTerm


Classes
^^^^^^^

.. autoclass:: Token
    :members:

.. autoclass:: WhitespaceToken
    :members:

.. autoclass:: StringToken
    :members:

.. autoclass:: OperatorToken
    :members:


Statements
----------

.. autoclass:: StatementContext
    :members:

.. autoclass:: StatementParser
    :members:

.. autoclass:: Statement
    :members:

Exceptions
^^^^^^^^^^

.. autoclass:: StatementSyntaxError
    :members:
