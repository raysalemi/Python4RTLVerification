import enum
from pyuvm import *

@enum.unique
class Ops(enum.IntEnum):
    """Legal ops for the TinyALU"""
    NOP = 0
    ADD = 1
    AND = 2
    XOR = 3
    MUL = 4

class AluCommand(uvm_transaction):

    def __init__(self, name, A=0, B=0, op=Ops.NOP):
        super().__init__(name)
        self.A = A
        self.B = B
        self.op = Ops(op)

    def __eq__(self, other):
        same = self.A == other.A \
               and self.B == other.B \
               and self.op == other.op
        return same

    def __str__(self):
        return f"{self.get_name()} : A: 0x{self.A:02x} OP: {self.op.name} ({self.op.value}) B: 0x{self.B:02x}"
    
    def randomize(self):
        self.A = random.randint(0,255)
        self.B = random.randint(0,255)
        self.op = random.choice(list(Ops))

class AluResult(uvm_transaction):
    def __init__(self, name, r):
        super().__init__(name)
        self.result = r

    def __str__(self):
        return f"{self.get_name()}: 0x{self.result:04x}"

    def __eq__(self, other):
        return self.result == other.result
