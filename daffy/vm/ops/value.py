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
"""`value` operation

`value` is a special operation that has no inputs and can be used to add
literal values to the operations table.
To create a `value` operation use the function :func:`DVM_value_create`

Inputs
------
`none`

Outputs
-------
value : value
    the literal value
"""

from daffy.vm.operations import OperationType, InputSocketType, OutputSocketType
from daffy.vm.operations import Operation
from daffy.vm.optypes import DVM_operation_type_register

# inputs and outputs
inputs = []

outputs = [
    OutputSocketType('value'),
]

# operation type definition
op = OperationType(
    name='value',
    inputs=inputs,
    outputs=outputs,
    execfunc=None
)

# function to create a `value` operation
def DVM_value_create(name, val):
    newval = Operation(op, name)
    newval.outputs[0].value = val
    newval.finished = True
    return newval

# register the operation
DVM_operation_type_register(op)

