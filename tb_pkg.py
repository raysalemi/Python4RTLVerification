import enum

@enum.unique
class Ops(enum.IntEnum):
    """Legal ops for the TinyALU"""
    NOP = 0
    ADD = 1
    AND = 2
    XOR = 3
    MUL = 4
