# Operation list
operations = []

def DVM_operation_register(op):
    if op not in operations:
        operations.append(op)


import value
from value import DVM_value_create
import add, sub, mul, div, printval
