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
from daffy.vm.interpreter import DVM_program_run

parser = OptionParser(usage="usage: %prog [options] file")
parser.add_option("-v", "--verbose",
                  action="store_true", default=False,
                  help="print debug messages to stderr")

(options, args) = parser.parse_args()

loglevel = options.verbose and logging.DEBUG or logging.NOTSET
logging.basicConfig(stream=sys.stderr, level=loglevel)

def main():
    """Parse args, setup a :class:`Scheduler` object, and use 
    :func:`DVM_program_run` to feed the contents of a **Daffy** file to the
    scheduler
    """
    if not len(args) == 1:
        parser.print_help()
        return 1
    else:
        filename = args[0]
    
    try:
        f = open(filename)
    except IOError, error:
        print("daffy: can't open file '%s': %s" % (filename, error))
        return 1
    
    scheduler = Scheduler(loglevel=loglevel)
    DVM_program_run(f, scheduler)
    f.close()

if __name__ == '__main__':
    main()
