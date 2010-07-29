# Operation types list
optypes = []

def DVM_operation_type_register(op):
    if op not in optypes:
        optypes.append(op)


import value
from value import DVM_value_create
import add, sub, mul, div, printval
