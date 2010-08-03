:mod:`cli` --- Command line interface
=====================================

.. this page doesn't use autodoc because importing a module named "cli"
   breaks sphinx-build, so the docstrings must be kept in sync manually

.. module:: cli
    :synopsis: Command line interface.

A command line interface to run *daffy* programs::

    Usage: daffy [options] [ -c cmd | file ]

    Options:
      -h, --help         show this help message and exit
      -v, --verbose      print debug messages to stderr
      -c CMD, --cmd=CMD  a single instruction

.. function:: main()

    Parse args, setup a :class:`Scheduler <daffy.vm.scheduler.Scheduler>`
    object, and use
    :func:`dvm_program_run() <daffy.vm.interpreter.dvm_program_run>` to feed it
    the contents of a *daffy* file.

