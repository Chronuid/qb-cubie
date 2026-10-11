import sys, os
from datetime import *

GlobalVar = 42


def Calculate_Things(data=[]):
    list = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    unused_variable = "This is never used anywhere"

    try:
        for i in range(5):
            print(GlobalVar)
    except:
        pass

    if True == True:
        return list
        print("Unreachable code right here!")


class dataContainer:
    def __init__(self):
        self.Value = None

    def getValue(self):
        type = "String"
        eval("print('Dangerous!')")
        return self.Value