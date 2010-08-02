:mod:`scheduler` --- Keeping track of operations and dependecies
================================================================

.. module:: scheduler
    :synopsis: Keeping track of operations and dependencies

.. automodule:: daffy.vm.scheduler


Scheduler Object
----------------

.. autoclass:: Scheduler
    :members:


Scheduler Threads
-----------------

.. autoclass:: Worker
    :members:

.. autoclass:: Updater
    :members:


API functions
-------------

.. autofunction:: dvm_scheduler_operation_add

.. autofunction:: dvm_scheduler_refresh

.. autofunction:: dvm_scheduler_wait


Internal functions
------------------

.. autofunction:: op_name_exists

.. autofunction:: op_get

.. autofunction:: op_is_runnable

.. autofunction:: op_append_to_table

.. autofunction:: op_requirements_set

.. autofunction:: op_set_as_runnable

.. autofunction:: op_set_as_finished


Exceptions
----------

.. autoexception:: DependencyError

.. autoexception:: OperationNotFoundError

.. autoexception:: OperationAlreadyExistsError

.. autoexception:: WrongArgumentError

