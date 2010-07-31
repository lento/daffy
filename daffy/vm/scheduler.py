# -*- coding: utf-8 -*-
#
# This file is part of Daffy.
#
# Daffy is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Daffy is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Daffy.  If not, see <http://www.gnu.org/licenses/>.
#
# Original Copyright (c) 2010, Lorenzo Pierfederici <lpierfederici@gmail.com>
# Contributor(s): 
#
"""The :class:`Scheduler` keeps track of operations and their dependency
relations.
    
Each operation in the table maintains a :attr:`Operation.waiting_on` counter of
its missing requirements (how many of its inputs are connected to operations
that have not been executed yet), and a :attr:`Operation.blocking` list of all
other operations that are waiting for its outputs to be ready.

When the :class:`Scheduler` is fed with an operation definition, it creates the
corresponding :class:`Operation` object, appends it to the table and, if all
of its requirements are ready (that is: if all the operations connected to its
inputs have already been executed), appends it to the
:attr:`Scheduler.runnable_queue`.

:class:`Worker` threads pick operations from :attr:`Scheduler.runnable_queue`,
execute them in parallel (as each runnable operation reads its inputs from
operations that have already been written to the table, there is no possible
racing on the values) and put them in the :attr:`Scheduler.finished_queue` when
done.

The :class:`Updater` thread picks operation from
:attr:`Scheduler.finished_queue`, notifies all operations waiting or it that
the output vaues are ready to use decreasing their :attr:`Scheduler.waiting_on`
counter and removing the finished operation from their
:attr:`Operation.blocking` list

The thread syncronization mechanism works like this::
    
    the scheduler is fed with operations
                 |
                 v
    `DVM_scheduler_operation_add`
    calls `op_append_to_table`
                 |
                 v
    if the operation must go through the
    execution engine a `token` is appended
    to the `waiting_counter` queue and the ------------------+
    opertaion itself is appended to                          |
    `runnable_queue` if all of its                           v
    requirements are ready                         `worker` threads pick
                 |                                 operations from the
                 v                                 `runnable_queue`, execute
    when all operations has been fed to the        them and append them to
    scheduler `DVM_scheduler_wait` is called       `finished_queue`
    At this point there is a token in                        |
    `waiting counter` for each operation that                v
    needs execution, so `DVM_scheduler_wait`     the `updater` thread waits  
    just waits for `waiting_counter` to be       for `tokens` to be put in
    empty                                        `waiting_counter`.
                 |                               When it gets a `token`,
                 |                               `updater` knows that there
                 |                               is an operation in the
                 |                               execution engine, so waits
                 |                               for it on `finished_queue`,
                 |                               notify its dependencies,
                 |                               and refresh the scheduler.
                 |                               Then removes a `token` from
                 |                               `waiting_counter`
                 |                                         |
                 +-----------------------------------------+
                 |
                 v
    `DVM_scheduler_wait` returns
"""

from threading import Thread, currentThread
from Queue import Queue
from daffy.vm.optypes import DVM_operation_type_find
from daffy.vm.operations import Operation, DVM_operation_exec
from daffy.vm.ops import DVM_value_create
from time import sleep

import sys, logging
logging.basicConfig(stream=sys.stderr, format='%(message)s')
log = logging.getLogger(__name__)


# Exceptions
class DependencyError(Exception):
    """Missing dependency"""


class OperationNotFoundError(Exception):
    """The operation was not found in the :attr:`Scheduler.opstable`"""


class OperationAlreadyExistsError(Exception):
    """The operation name already exists in the :attr:`Scheduler.opstable`"""


class WrongArgumentError(Exception):
    """Wrong argument in operation creation"""


#: number of :class:`Worker` threads
WORKERS = 4

# an empty object used to count operations in the ``waiting_counter`` queue
TOKEN = None

# scheduler phases constants used in logging
SPACER = '..'
ADDING    = 0
RUNNING   = 1
EXECUTING = 2
FINISHING = 3
UPDATING  = 4

class Worker(Thread):
    """A worker thread that execute operations from the
    :attr:`Scheduler.runnable_queue` of a given :class:`Scheduler` object
    """
    def __init__(self, scheduler):
        Thread.__init__(self)
        
        #: the :class:`Scheduler` object this thread belongs to
        self.scheduler = scheduler

    def run(self):
        while True:
            op = self.scheduler.runnable_queue.get()
            log.debug('< %15s > %sexecuting in thread %s' % (
                            op.name, SPACER * EXECUTING, currentThread().name))
            DVM_operation_exec(op)
            self.scheduler.finished_queue.put(op)
            self.scheduler.runnable_queue.task_done()


class Updater(Thread):
    """A coordination thread that updates dependencies once an
    :class:`Operation` has finished
    """
    def __init__(self, scheduler):
        Thread.__init__(self)

        #: the :class:`Scheduler` object this thread belongs to
        self.scheduler = scheduler

    def run(self):
        sched = self.scheduler
        while True:
            sched.waiting_counter.get()
            op = sched.finished_queue.get(timeout=5)
            op_set_as_finished(op, sched)
            DVM_scheduler_refresh(sched)
            sched.finished_queue.task_done()
            sched.waiting_counter.task_done()


# Scheduler
class Scheduler(object):
    """A :class:`Scheduler` object keeps a table of all operations and various
    queues for thread syncronization
    
    .. seealso::
        :mod:`scheduler` for a detailed description
    """
    def __init__(self, loglevel=logging.NOTSET):
        log.level = loglevel
        
        #: this is the :class:`Scheduler`'s main data structure, a list of all
        #: operations fed to it
        self.opstable = []
        
        #: counter used by :func:`DVM_scheduler_wait` for thread syncronization
        self.waiting_counter = Queue()
        
        #: queue of operations that can be executed immediatly, as all their
        #: requirements are ready
        self.runnable_queue = Queue()
        
        #: queue of operations already executed by a :class:`Worker` thread and
        #: ready to be updated by the :class:`Updater` thread
        self.finished_queue = Queue()

        self._updater = Updater(self)
        self._updater.daemon = True
        self._updater.start()

        self._workers = []
        for i in range(WORKERS):
             w = Worker(self)
             w.daemon = True
             self._workers.append(w)
             w.start()


# internal use
def op_name_exists(name, scheduler):
    """Check if a name is already used in the :attr:`Scheduler.opstable`"""
    for op in scheduler.opstable:
        if op.name == name:
            return True
    return False

def op_get(name, scheduler):
    """Find and operation by name in the :attr:`Scheduler.opstable`"""
    for op in scheduler.opstable:
        if op.name == name:
            return op
    raise OperationNotFoundError(name)

def op_is_runnable(op, scheduler):
    """Check if an :class:`Operation` object is runnable verifing its counter of
    missing requirements"""
    return op.waiting_on == 0

def op_append_to_table(op, scheduler, waiting=True):
    """Append an :class:`Operation` object to the :attr:`Scheduler.opstable`"""
    log.debug('< %15s > %sadding to opstable' % (op.name, SPACER * ADDING))
    scheduler.opstable.append(op)
    if waiting:
        scheduler.waiting_counter.put(TOKEN)
    else:
        op_set_as_finished(op, scheduler)

def op_requirements_set(op, scheduler):
    """Loop over an :class:`Operation` object inputs and set its requirements"""
    waiting = 0
    for insock in op.inputs:
        if insock.op and insock.op not in scheduler.opstable:
            raise DependencyError
        if insock.op and not insock.op.finished:
            waiting += 1
            if op not in insock.op.blocking:
                insock.op.blocking.append(op)
    op.waiting_on = waiting

def op_set_as_runnable(op, scheduler):
    """Append the operations to the :attr:`Scheduler.runnable_queue`.
    :class:`Worker` threads will pick operations from this queue and execute
    them
    """
    log.debug('< %15s > %ssetting as runnable' % (op.name, SPACER * RUNNING))
    scheduler.runnable_queue.put(op)

def op_set_as_finished(op, scheduler):
    """Notify other operations depending on this one that it has finished
    executing and its ouputs are ready for use
    """
    outputs = ', '.join(['%s=%s' % (o.name, o.value) for o in op.outputs])
    log.debug('< %15s > %ssetting as finished (%s)' % (
                                        op.name, SPACER * FINISHING, outputs))
    op.finished = True
    log.debug('< %15s > %supdating dependencies' % (op.name, SPACER * UPDATING))
    for i in range(len(op.blocking)):
        dep = op.blocking.pop()
        dep.waiting_on -= 1


# API
def DVM_scheduler_operation_add(type, name, args, scheduler):
    """Create an :class:`Operation` object, resolve its requirements and add it
    to the :attr:`Scheduler.opstable`
    
    If all of its requirements are ready, append the operation to the
    :attr:`Scheduler.runnable_queue` straight away, otherwise it will be
    scheduled as runnable by the :class:`Updater` thread with
    :func:`DVM_scheduler_refresh`
    """
    optype = DVM_operation_type_find(type)
    if op_name_exists(name, scheduler):
        raise OperationAlreadyExistsError(name)

    inputs = []

    if type == 'value':
        if len(args) == 1 and len(args[0]) == 2:
            arg_name, value = args[0]
            if isinstance(value, float):
                op = DVM_value_create(name, value)
                # this operation doesn't need to go through the engine, so we
                # put "waiting=False" and don't set is as "runnable"
                op_append_to_table(op, scheduler, waiting=False)
            else:
                raise WrongArgumentError(value)
        else:
            raise WrongArgumentError(args[0])
    else:
        for i, arg in enumerate(args):
            if len(arg) == 2:
                arg_name, arg_value = arg
                valueop_name = '_%s_arg_%i' % (name, i)
                valueop_args = (('value', arg_value), )
                DVM_scheduler_operation_add('value', valueop_name,
                                                        valueop_args, scheduler)
                target = op_get(valueop_name, scheduler)
                inputs.append((arg_name, target, 'value'))
            elif len(arg) == 3:
                arg_name, target_name, attr = arg
                target = op_get(target_name, scheduler)
                inputs.append((arg_name, target, attr))
            else:
                raise WrongArgumentError(arg)

        op = Operation(optype, name, inputs)
        op_append_to_table(op, scheduler)
        op_requirements_set(op, scheduler)

        # if all requirements are ready we set it as "runnable" stright away
        # otherwise it will be set as "runnable" by DVM_scheduler_refresh
        if op_is_runnable(op, scheduler):
            op_set_as_runnable(op, scheduler)

def DVM_scheduler_refresh(scheduler):
    """Find which operations in the :attr:`Scheduler.opstable` can be run and
    append them to the :attr:`Scheduler.runnable_queue`"""
    for op in scheduler.opstable:
        if not op.finished and op_is_runnable(op, scheduler):
            op_set_as_runnable(op, scheduler)

def DVM_scheduler_wait(scheduler):
    """Wait for all operations to execute joining the scheduler's
    ``waiting_counter`` queue
    
    .. seealso::
        :mod:`scheduler` for a detaild description of thread syncronization
    """
    scheduler.waiting_counter.join()
    log.debug('all operations have finished')

