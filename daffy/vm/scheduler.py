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
"""Scheduler module"""

from threading import Thread
from Queue import Queue
from daffy.vm.optypes import DVM_operation_type_find
from daffy.vm.operations import Operation, DVM_operation_exec
from daffy.vm.ops import DVM_value_create


# Exceptions
class DependencyError(Exception):
    """Missing dependency"""


class OperationNotFoundError(Exception):
    """The operation was not found in the scheduler table"""


class OperationAlreadyExistsError(Exception):
    """The operation name already exists in the scheduler table"""


class WrongArgumentError(Exception):
    """Wrong argument in operation creation"""


# multi-threaded engine
THREADS = 4

class Worker(Thread):
    """A worker thread that execute operations from the `runnables` queue of
    a give scheduler
    """
    def __init__(self, scheduler):
        Thread.__init__(self)
        self.scheduler = scheduler

    def run(self):
        while True:
            op = self.scheduler.runnables.get()
            if callable(op.typeinfo.execfunc):
                print('DEBUG: %s executing' % op)
                DVM_operation_exec(op)
            else:
                print('DEBUG: %s doesn\'t need to be executed' % op)
            self.scheduler.finished.put(op)
            self.scheduler.runnables.task_done()


class Updater(Thread):
    """A coordination thread that updates dependencies once an operation has
    finished
    """
    def __init__(self, scheduler):
        Thread.__init__(self)
        self.scheduler = scheduler

    def run(self):
        while True:
            op = self.scheduler.finished.get()
            print('DEBUG: %s updating dependencies' % op)
            op_set_as_finished(op, self.scheduler)
            DVM_scheduler_refresh(self.scheduler)
            self.scheduler.finished.task_done()


# Scheduler
class Scheduler(object):
    """A `Scheduler` object keeps a table of all operations and a queue of
    operations that can be run, as all their dependancies are ready"""
    def __init__(self):
        self.operations = []
        self.runnables = Queue()
        self.finished = Queue()
        u = Updater(self)
        u.daemon = True
        u.start()
        for i in range(THREADS):
             t = Worker(self)
             t.daemon = True
             t.start()


def scheduler_operation_run(op, scheduler):
    print('DEBUG: %s adding operation to runnables queue' % op)
    scheduler.runnables.put(op)

def op_name_exists(name, scheduler):
    for op in scheduler.operations:
        if op.name == name:
            return True
    return False

def op_requirements_set(op, scheduler):
    """Loop over an operation inputs and set its requirements"""
    waiting = 0
    for insock in op.inputs:
        if insock.op and insock.op not in scheduler.operations:
            raise DependencyError
        if insock.op and not insock.op.finished:
            waiting += 1
            if op not in insock.op.blocking:
                insock.op.blocking.append(op)
    op.waiting_on = waiting

def op_is_runnable(op, scheduler):
    """Check if an operation is runnable"""
    return op.waiting_on == 0

def op_set_as_finished(op, scheduler):
    """Notify operations depending on `op` that its ouputs are ready"""
    op.finished = True
    for i in range(len(op.blocking)):
        dep = op.blocking.pop()
        dep.waiting_on -= 1


# API
def DVM_scheduler_operation_find(name, scheduler):
    """Find and operation by name in the scheduler's `opstable`"""
    for op in scheduler.operations:
        if op.name == name:
            return op
    raise OperationNotFoundError(name)

def DVM_scheduler_operation_add(type, name, args, scheduler):
    """Create an operation, resolve its dependencies and add it to the
    scheduler's `opstable` (and to the `runnables` queue if all of its
    dependencies are ready)
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
                target = DVM_scheduler_operation_find(valueop_name, scheduler)
                inputs.append((arg_name, target, 'value'))
            elif len(arg) == 3:
                arg_name, target_name, attr = arg
                target = DVM_scheduler_operation_find(target_name, scheduler)
                inputs.append((arg_name, target, attr))
            else:
                raise WrongArgumentError(arg)
        op = Operation(optype, name, inputs)

    scheduler.operations.append(op)
    runnable = True
    op_requirements_set(op, scheduler)
    if op_is_runnable(op, scheduler):
        scheduler_operation_run(op, scheduler)

def DVM_scheduler_reset(scheduler):
    """Reset a scheduler to its initial state"""
    scheduler.operations = []
    scheduler.runnables = []

def DVM_scheduler_refresh(scheduler):
    """Find which operations in the scheduler's `opstable` can be run and puts
    them in the `runnables` queue"""
    for op in scheduler.operations:
        if not op.finished and op_is_runnable(op, scheduler):
            scheduler_operation_run(op, scheduler)


