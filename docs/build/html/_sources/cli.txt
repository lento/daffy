:mod:`cli` --- Command line interface
=====================================

.. this page doesn't use autodoc because importing a module named "cli"
   breaks sphinx-build

.. module:: cli
    :synopsis: Command line interface.

A command line interface to run **Daffy** programs from files

.. function:: main()

    Parse args, setup a :class:`Scheduler` object, and use 
    :func:`dvm_program_run` to feed the contents of a Daffy file to the
    scheduler
