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
"""Operations module"""

# Exceptions
class OperationError(Exception):
    """Operation error"""


class InputSocketNotFoundError(OperationError):
    """Error raised when an InputSocket is not found"""


class OutputSocketNotFoundError(OperationError):
    """Error raised when an OutputSocket is not found"""


# Inputs
class InputSocketType(object):
    def __init__(self, name, default):
        self.name = name
        self.default = default

    def __repr__(self):
        return '<InputSocketType: %s (%s)>' % (self.name, self.default)


class InputSocket(object):
    def __init__(self, type, op, attr):
        self.type = type
        self.op = op
        self.attr = attr
        
        self.name = type.name
        self.value = type.default

    def __repr__(self):
        conn = self.op and '%s.%s' % (self.op.name, self.attr) or ''
        return '<InputSocket: %s (%s)>' % (self.name, conn)


# Outputs
class OutputSocketType(object):
    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return '<OutputSocketType: %s>' % (self.name)


class OutputSocket(object):
    def __init__(self, type):
        self.type = type
        
        self.name = type.name
        self.value = None

    def __repr__(self):
        return '<OutputSocket: %s (%s)>' % (self.name, self.value)


# Operations
class OperationType(object):
    """Parent class for daffy operations
    
    Operations must define their inputs and outputs and implement the
    :execfunc: method
    """
    def __init__(self, name, inputs, outputs, execfunc):
        self.name = name
        self.inputs = inputs
        self.outputs = outputs
        self.execfunc = execfunc

    def __repr__(self):
        return '<OperationType: %s>' % self.name


class Operation(object):
    def __init__(self, type, name, inputs=[]):
        self.typeinfo = type
        self.name = name
        self.waiting_on = 0
        self.blocking = []
        self.finished = False
        
        self.inputs = []
        for in_type in type.inputs:
            sock = InputSocket(in_type, None, None)
            self.inputs.append(sock)
            for in_name, in_op, in_attr in inputs:
                if in_name == sock.name:
                    sock.op = in_op
                    sock.attr = in_attr
        
        self.outputs = []
        for out_type in type.outputs:
            self.outputs.append(OutputSocket(out_type))
        
    def __repr__(self):
        return '<Operation: %s (%s)>' % (self.name, self.typeinfo.name)


# API
def DVM_input_socket(op, name):
    for socket in op.inputs:
        if socket.name == name:
            return socket
    raise InputSocketNotFoundError(name)

def DVM_input_value_get(op, name):
    sock = DVM_input_socket(op, name)
    if sock.op:
        source = DVM_output_socket(sock.op, sock.attr)
        return source.value
    else:
        return sock.typeinfo.default

def DVM_output_socket(op, name):
    for socket in op.outputs:
        if socket.name == name:
            return socket
    raise OutputSocketNotFoundError(name)

def DVM_operation_exec(op):
    """Run the operation `execfunc`"""
    op.typeinfo.execfunc(op)

