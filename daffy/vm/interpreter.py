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
"""Interpreter module

This is a basic interpreter for Daffy assembly code.
The interpreter expects lines in the form::

    $name: optype([argname=$target.attr | <float value>], ...)
"""

import re
from daffy.vm.optypes import optypes
from daffy.vm.scheduler import DVM_scheduler_operation_add

# Exceptions
class ParserSyntaxError(Exception):
    """A syntax error"""


class ParserUndefinedState(Exception):
    """The parser reached an undefined state"""


# parser states
NEW         =  0
DOLLAR      =  1
NAME        =  2
OPTYPE      =  3
ARGS        =  4
ARGS_NAME   =  5
ARGS_EQUAL  =  6
ARGS_DOLLAR =  7
ARGS_TARGET =  8
ARGS_DOT    =  9
ARGS_ATTR   = 10
ARGS_FLOAT  = 11

def DVM_line_parse(line):
    """Parse a line of input"""
    state = NEW
    AFTER_COLON = False
    AFTER_COMMA = False
    FLOAT_DECIMAL = False

    name = ''
    optype = ''
    args = []
    arg_name = ''
    arg_target = ''
    arg_attr = ''
    arg_float = ''
    
    for i, c in enumerate(line):
        if (AFTER_COLON or AFTER_COMMA) and re.match(r'\s', c):
            pass    # ignore whitespace
        elif state == NEW:
            if c == '$':
                state = DOLLAR
            else:
                index = '%s^' % ('-' * i)
                error = 'at char %i: expecting "$"' % i
                raise ParserSyntaxError('\n%s\n%s\n%s' % (line, index, error))
        elif state == DOLLAR:
            if re.match(r'[a-zA-Z]', c):
                name += c
                state = NAME
            else:
                index = '%s^' % ('-' * i)
                error = 'at char %i: expecting an operation name' % i
                raise ParserSyntaxError('\n%s\n%s\n%s' % (line, index, error))
        elif state == NAME:
            if re.match(r'[a-zA-Z0-9_]', c):
                name += c
            elif c == ':':
                state = OPTYPE
                AFTER_COLON = True
            else:
                index = '%s^' % ('-' * i)
                error = 'at char %i: expecting ":"' % i
                raise ParserSyntaxError('\n%s\n%s\n%s' % (line, index, error))
        elif state == OPTYPE:
            if re.match(r'[a-zA-Z]', c):
                AFTER_COLON = False
                optype += c
            elif c == '(':
                state = ARGS
            else:
                index = '%s^' % ('-' * i)
                error = 'at char %i: expecting an operation type' % i
                raise ParserSyntaxError('\n%s\n%s\n%s' % (line, index, error))
        elif state == ARGS:
            if re.match(r'[a-zA-Z]', c):
                arg_name += c
                state = ARGS_NAME
            elif c == ')':
                # the operation definition ended, we ignore the rest of the
                # line, so it can be used for comments
                break
            else:
                index = '%s^' % ('-' * i)
                error = 'at char %i: expecting an argument name or ")"' % i
                raise ParserSyntaxError('\n%s\n%s\n%s' % (line, index, error))
        elif state == ARGS_NAME:
            if re.match(r'[a-zA-Z0-9_]', c):
                arg_name += c
            elif c == '=':
                state = ARGS_EQUAL
            else:
                index = '%s^' % ('-' * i)
                error = 'at char %i: expecting "="' % i
                raise ParserSyntaxError('\n%s\n%s\n%s' % (line, index, error))
        elif state == ARGS_EQUAL:
            if c == '$':
                state = ARGS_DOLLAR
            elif re.match(r'[0-9]', c):
                arg_float += c
                state = ARGS_FLOAT
            else:
                index = '%s^' % ('-' * i)
                error = 'at char %i: expecting a literal value or "$"' % i
                raise ParserSyntaxError('\n%s\n%s\n%s' % (line, index, error))
        elif state == ARGS_DOLLAR:
            if re.match(r'[a-zA-Z]', c):
                arg_target += c
                state = ARGS_TARGET
            else:
                index = '%s^' % ('-' * i)
                error = 'at char %i: expecting an operation name' % i
                raise ParserSyntaxError('\n%s\n%s\n%s' % (line, index, error))
        elif state == ARGS_TARGET:
            if re.match(r'[a-zA-Z0-9_]', c):
                AFTER_COMMA = False
                arg_target += c
            elif c == '.':
                state = ARGS_DOT
            else:
                index = '%s^' % ('-' * i)
                error = 'at char %i: expecting "."' % i
                raise ParserSyntaxError('\n%s\n%s\n%s' % (line, index, error))
        elif state == ARGS_DOT:
            if re.match(r'[a-zA-Z]', c):
                arg_attr += c
                state = ARGS_ATTR
            else:
                index = '%s^' % ('-' * i)
                error = 'at char %i: expecting an attribute name' % i
                raise ParserSyntaxError('\n%s\n%s\n%s' % (line, index, error))
        elif state == ARGS_ATTR:
            if re.match(r'[a-zA-Z0-9_]', c):
                arg_attr += c
            elif c == ',':
                args.append((arg_name, arg_target, arg_attr))
                arg_name = arg_target = arg_attr = ''
                AFTER_COMMA = True
                state = ARGS
            elif c == ')':
                # the operation definition ended, we ignore the rest of the
                # line, so it can be used for comments
                args.append((arg_name, arg_target, arg_attr))
                arg_name = arg_target = arg_attr = ''
                break
            else:
                index = '%s^' % ('-' * i)
                error = 'at char %i: expecting "," or ")"' % i
                raise ParserSyntaxError('\n%s\n%s\n%s' % (line, index, error))
        elif state == ARGS_FLOAT:
            if c == ',':
                args.append((arg_name, float(arg_float)))
                arg_name = arg_float = ''
                AFTER_COMMA = True
                state = ARGS
            elif c == ')':
                # the operation definition ended, we ignore the rest of the
                # line, so it can be used for comments
                args.append((arg_name, float(arg_float)))
                arg_name = arg_float = ''
                break
            elif c == '.':
                if FLOAT_DECIMAL:
                    index = '%s^' % ('-' * i)
                    error = 'at char %i: expecting  a digit, "," or ")"' % i
                    raise ParserSyntaxError('\n%s\n%s\n%s' % (line, index, error))
                else:
                    arg_float += c
                    FLOAT_DECIMAL = True
            elif re.match(r'[0-9]', c):
                arg_float += c
            else:
                index = '%s^' % ('-' * i)
                error = 'at char %i: expecting a digit, "," or ")"' % i
                raise ParserSyntaxError('\n%s\n%s\n%s' % (line, index, error))
        else:
            raise ParserUndefinedState(state)
    
    return optype, name, args

def DVM_instruction_run(instruction, scheduler):
    """Parse an instruction and schedule the resulting operation for
    execution
    """
    optype, name, args = DVM_line_parse(instruction)
    DVM_scheduler_operation_add(optype, name, args, scheduler)

def DVM_program_run(program, scheduler):
    """Run a Daffy program"""
    for instruction in program:
        DVM_instruction_run(instruction, scheduler)

