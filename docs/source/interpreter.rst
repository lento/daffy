:mod:`interpreter` --- Parsing instructions and feeding the :mod:`scheduler`
============================================================================

.. module:: interpreter
    :synopsis: Parsing instructions and feeding the :mod:`Scheduler`

.. automodule:: daffy.vm.interpreter

API functions
-------------

.. autofunction:: DVM_instruction_run

.. autofunction:: DVM_program_run


Internal functions
------------------

.. autofunction:: instruction_parse

.. autofunction:: instruction_schedule


Exceptions
----------

.. autoexception:: ParserSyntaxError

.. autoexception:: ParserUndefinedState

