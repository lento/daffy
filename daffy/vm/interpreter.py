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
"""This is a basic interpreter for Daffy assembly code.
The interpreter expects instructions in the form::

    $name: optype([argname=$target.attr | <float value>], ...)

one instruction per line.
"""

import re, sys, logging
from daffy.vm.optypes import optypes
from daffy.vm.scheduler import DVM_scheduler_operation_add, DVM_scheduler_wait

logging.basicConfig(stream=sys.stderr, level=logging.ERROR)
log = logging.getLogger(__name__)

# Exceptions
class ParserSyntaxError(Exception):
    """A syntax error"""


class ParserUndefinedState(Exception):
    """The parser reached an undefined state"""


# parser states
START         =  0
DOLLAR        =  1
NAME          =  2
COLON         =  3
OPTYPE        =  4
ARGS          =  5
ARGS_NAME     =  6
ARGS_EQUAL    =  7
ARGS_DOLLAR   =  8
ARGS_TARGET   =  9
ARGS_DOT      = 10
ARGS_ATTR     = 11
ARGS_COMMA    = 12
ARGS_FLOAT    = 13
FLOAT_DOT     = 14
FLOAT_DECIMAL = 15

# internal use
def instruction_parse(instr):
    """Parse an instruction"""
    state = START

    name = ''
    optype = ''
    args = []
    arg_name = ''
    arg_target = ''
    arg_attr = ''
    arg_float = ''
    
    for i, c in enumerate(instr):
        if state == START:
            if c == '$':
                state = DOLLAR
            else:
                pos = '%s^' % ('-' * i)
                err = 'at char %i: expecting "$"' % i
                raise ParserSyntaxError('\n%s\n%s\n%s' % (instr, pos, err))
        elif state == DOLLAR:
            if re.match(r'[a-zA-Z]', c):
                name += c
                state = NAME
            else:
                pos = '%s^' % ('-' * i)
                err = 'at char %i: expecting an operation name' % i
                raise ParserSyntaxError('\n%s\n%s\n%s' % (instr, pos, err))
        elif state == NAME:
            if re.match(r'[a-zA-Z0-9_]', c):
                name += c
            elif c == ':':
                state = COLON
            else:
                pos = '%s^' % ('-' * i)
                err = 'at char %i: expecting ":"' % i
                raise ParserSyntaxError('\n%s\n%s\n%s' % (instr, pos, err))
        elif state == COLON:
            if re.match(r'\s', c):
                pass    # ignore whitespace
            elif re.match(r'[a-zA-Z]', c):
                optype += c
                state = OPTYPE
            else:
                pos = '%s^' % ('-' * i)
                err = 'at char %i: expecting an operation type' % i
                raise ParserSyntaxError('\n%s\n%s\n%s' % (instr, pos, err))
        elif state == OPTYPE:
            if re.match(r'[a-zA-Z0-9_]', c):
                optype += c
            elif c == '(':
                state = ARGS
            else:
                pos = '%s^' % ('-' * i)
                err = 'at char %i: expecting an operation type' % i
                raise ParserSyntaxError('\n%s\n%s\n%s' % (instr, pos, err))
        elif state == ARGS:
            if re.match(r'[a-zA-Z]', c):
                arg_name += c
                state = ARGS_NAME
            elif c == ')':
                # the operation definition ended, we ignore the rest of the
                # instruction, so it can be used for comments
                break
            else:
                pos = '%s^' % ('-' * i)
                err = 'at char %i: expecting an argument name or ")"' % i
                raise ParserSyntaxError('\n%s\n%s\n%s' % (instr, pos, err))
        elif state == ARGS_NAME:
            if re.match(r'[a-zA-Z0-9_]', c):
                arg_name += c
            elif c == '=':
                state = ARGS_EQUAL
            else:
                pos = '%s^' % ('-' * i)
                err = 'at char %i: expecting "="' % i
                raise ParserSyntaxError('\n%s\n%s\n%s' % (instr, pos, err))
        elif state == ARGS_EQUAL:
            if c == '$':
                state = ARGS_DOLLAR
            elif re.match(r'[0-9]', c):
                arg_float += c
                state = ARGS_FLOAT
            else:
                pos = '%s^' % ('-' * i)
                err = 'at char %i: expecting "$" or a literal value' % i
                raise ParserSyntaxError('\n%s\n%s\n%s' % (instr, pos, err))
        elif state == ARGS_DOLLAR:
            if re.match(r'[a-zA-Z]', c):
                arg_target += c
                state = ARGS_TARGET
            else:
                pos = '%s^' % ('-' * i)
                err = 'at char %i: expecting an operation name' % i
                raise ParserSyntaxError('\n%s\n%s\n%s' % (instr, pos, err))
        elif state == ARGS_TARGET:
            if re.match(r'[a-zA-Z0-9_]', c):
                arg_target += c
            elif c == '.':
                state = ARGS_DOT
            else:
                pos = '%s^' % ('-' * i)
                err = 'at char %i: expecting "."' % i
                raise ParserSyntaxError('\n%s\n%s\n%s' % (instr, pos, err))
        elif state == ARGS_DOT:
            if re.match(r'[a-zA-Z]', c):
                arg_attr += c
                state = ARGS_ATTR
            else:
                pos = '%s^' % ('-' * i)
                err = 'at char %i: expecting an attribute name' % i
                raise ParserSyntaxError('\n%s\n%s\n%s' % (instr, pos, err))
        elif state == ARGS_ATTR:
            if re.match(r'[a-zA-Z0-9_]', c):
                arg_attr += c
            elif c == ',':
                args.append((arg_name, arg_target, arg_attr))
                arg_name = arg_target = arg_attr = ''
                state = ARGS_COMMA
            elif c == ')':
                # the operation definition ended, we ignore the rest of the
                # instruction, so it can be used for comments
                args.append((arg_name, arg_target, arg_attr))
                arg_name = arg_target = arg_attr = ''
                break
            else:
                pos = '%s^' % ('-' * i)
                err = 'at char %i: expecting "," or ")"' % i
                raise ParserSyntaxError('\n%s\n%s\n%s' % (instr, pos, err))
        elif state == ARGS_COMMA:
            if re.match(r'\s', c):
                pass    # ignore whitespace
            elif re.match(r'[a-zA-Z]', c):
                arg_name += c
                state = ARGS_NAME
            else:
                pos = '%s^' % ('-' * i)
                err = 'at char %i: expecting an argument name' % i
                raise ParserSyntaxError('\n%s\n%s\n%s' % (instr, pos, err))
        elif state == ARGS_FLOAT:
            if re.match(r'[0-9]', c):
                arg_float += c
            elif c == '.':
                arg_float += c
                state = FLOAT_DOT
            elif c == ',':
                args.append((arg_name, float(arg_float)))
                arg_name = arg_float = ''
                state = ARGS_COMMA
            elif c == ')':
                # the operation definition ended, we ignore the rest of the
                # instruction, so it can be used for comments
                args.append((arg_name, float(arg_float)))
                arg_name = arg_float = ''
                break
            else:
                pos = '%s^' % ('-' * i)
                err = 'at char %i: expecting a digit, ".", "," or ")"' % i
                raise ParserSyntaxError('\n%s\n%s\n%s' % (instr, pos, err))
        elif state == FLOAT_DOT:
            if re.match(r'[0-9]', c):
                arg_float += c
                state = FLOAT_DECIMAL
            else:
                pos = '%s^' % ('-' * i)
                err = 'at char %i: expecting a digit' % i
                raise ParserSyntaxError('\n%s\n%s\n%s' % (instr, pos, err))
        elif state == FLOAT_DECIMAL:
            if re.match(r'[0-9]', c):
                arg_float += c
            elif c == ',':
                args.append((arg_name, float(arg_float)))
                arg_name = arg_float = ''
                state = ARGS_COMMA
            elif c == ')':
                # the operation definition ended, we ignore the rest of the
                # instruction, so it can be used for comments
                args.append((arg_name, float(arg_float)))
                arg_name = arg_float = ''
                break
            else:
                pos = '%s^' % ('-' * i)
                err = 'at char %i: expecting a digit, "," or ")"' % i
                raise ParserSyntaxError('\n%s\n%s\n%s' % (instr, pos, err))
        else:
            raise ParserUndefinedState(state)
    
    return optype, name, args

def instruction_schedule(instruction, scheduler):
    """Parse an instruction and schedule the resulting operation for
    execution
    """
    try:
        optype, name, args = instruction_parse(instruction)
        DVM_scheduler_operation_add(optype, name, args, scheduler)
    except ParserSyntaxError, error:
        log.error('SyntaxError: %s' % error)
        return 1
    return 0


# API
def DVM_instruction_run(instruction, scheduler):
    """Run a single instruction"""
    retval = instruction_schedule(instruction, scheduler)
    DVM_scheduler_wait(scheduler)
    return retval

def DVM_program_run(program, scheduler):
    """Run a Daffy program"""
    result = 0
    for instruction in program:
        result += instruction_schedule(instruction, scheduler)
    DVM_scheduler_wait(scheduler)
    return result == 0 and 0 or 1


