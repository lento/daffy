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

class DependencyError(Exception):
    """missing dependency"""

class Scheduler(object):
    """Schedules operations for execution"""
    operations = []
    runnables = []
    
def scheduler_operation_add(scheduler, op):
    scheduler.operations.append(op)
    runnable = True
    for name, i in op.inputs.iteritems():
        if i.op and i.op not in scheduler.operations:
            raise DependencyError
        if i.op and not i.op.ready:
            runnable = False
            op.waiting_on += 1
            i.op.blocking.append(op)
    if runnable:
        scheduler_operation_run(scheduler, op)
                
def scheduler_operation_run(scheduler, op):
    scheduler.runnables.append(op)


