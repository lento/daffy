#!/usr/bin/env python
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
"""A command line interface to run **Daffy** programs from files
"""

import sys, logging
from optparse import OptionParser
from daffy.vm.scheduler import Scheduler
from daffy.vm.interpreter import dvm_program_run, dvm_instruction_run

parser = OptionParser(usage="usage: %prog [options] [ -c cmd | file ]")
parser.add_option("-v", "--verbose",
                  action="store_true", default=False,
                  help="print debug messages to stderr")
parser.add_option("-c", "--cmd",
                  default=None,
                  help="a single instruction")

(options, args) = parser.parse_args()

loglevel = options.verbose and logging.DEBUG or logging.NOTSET
logging.basicConfig(stream=sys.stderr, level=loglevel)

def main():
    """Parse args, setup a :class:`Scheduler` object, and use 
    :func:`dvm_program_run` to feed the contents of a **Daffy** file to the
    scheduler
    """
    scheduler = Scheduler(loglevel=loglevel)

    if options.cmd and len(args) == 0:          # called with -c
        retval = dvm_instruction_run(options.cmd, scheduler)
        return retval
    elif not options.cmd and len(args) == 1:    # called with a file
        filename = args[0]
        try:
            f = open(filename)
        except IOError, error:
            print("daffy: can't open file '%s': %s" % (filename, error))
            return 1
        retval = dvm_program_run(f, scheduler)
        f.close()
        return retval
    else:
        parser.print_help()
        return 1

if __name__ == '__main__':
    main()

