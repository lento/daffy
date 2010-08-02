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
"""`add` operation

The `add` operation sums two values.

Inputs
------
a : value
    the first value
b : value
    the second value

Outputs
-------
result : value
    the sum of `a` and `b`
"""

from daffy.vm.operations import OperationType, InputSocketType, OutputSocketType
from daffy.vm.operations import dvm_input_value_get, dvm_output_socket
from daffy.vm.optypes import dvm_operation_type_register

# inputs and outputs
inputs = [
    InputSocketType('a', 0.0),
    InputSocketType('b', 0.0),
]

outputs = [
    OutputSocketType('result'),
]

# execfunc
def execfunc(self):
    a = dvm_input_value_get(self, 'a')
    b = dvm_input_value_get(self, 'b')
    out_result = dvm_output_socket(self, 'result')

    out_result.value = a + b

# operation type definition
op = OperationType(
    name='add',
    inputs=inputs,
    outputs=outputs,
    execfunc=execfunc
)

# register the operation
dvm_operation_type_register(op)
