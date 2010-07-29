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
"""Operation types module

This module defines the `optypes` list and API functions used to manage
operation types.
"""

# Exceptions
class OperationTypeNotFoundError(Exception):
    """Operation error"""


# Operation types list
optypes = []

def DVM_operation_type_register(op):
    """Register a new type in the `optypes` list"""
    if op not in optypes:
        optypes.append(op)

def DVM_operation_type_find(type):
    """Return an optype from the list of registered types"""
    for optype in optypes:
        if optype.name == type:
            return optype
    raise OperationTypeNotFoundError(type)


# Load optypes and populate the list, beware of import dependency issue
import daffy.vm.ops

