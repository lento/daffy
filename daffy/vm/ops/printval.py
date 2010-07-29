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
"""`print` operation

The `print` operation prints a value to standard output.

Inputs
------
value : value
    the value to be printed

Outputs
-------
`none`
"""

from daffy.vm.operations import OperationType, InputSocketType, OutputSocketType
from daffy.vm.ops import DVM_operation_type_register

# inputs and outputs
inputs = [
    InputSocketType('value', 0.0),
]

outputs = []

# execfunc
def execfunc(self):
    val = DVM_input_value_get(self, 'value')

    print(val)

# operation type definition
op = OperationType(
    name='print',
    inputs=inputs,
    outputs=outputs,
    execfunc=execfunc
)

# register the operation
DVM_operation_type_register(op)

