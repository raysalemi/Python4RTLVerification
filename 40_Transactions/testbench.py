import cocotb
from pyuvm import *
import random
# All testbenches use tinyalu_utils, so store it in a central
# place and add its path to the sys path so we can import it
import sys
from pathlib import Path
sys.path.append(str(Path("..").resolve()))
from tinyalu_utils import Ops  # noqa:E402
# Mailbox example


class AluCommand(uvm_transaction):

    def __init__(self, name, A=0, B=0, op=Ops.ADD):
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
        return f"{self.get_name()} : A: {self.A:02x} OP: {self.op.name} ({self.op.value}) B: {self.B:02x}"

    def randomize(self):
        self.A = random.randint(0, 255)
        self.B = random.randint(0, 255)
        self.op = random.choice(list(Ops))


class AluResult(uvm_transaction):
    def __init__(self, name, r):
        super().__init__(name)
        self.result = r

    def __str__(self):
        return f"{self.get_name()}: {self.result:04x}"

    def __eq__(self, other):
        return self.result == other.result


@cocotb.test()
async def alu_command(dut):
    """Exercise the ALUCommand Transaction"""
    op1 = AluCommand("op1", A=0x25, B=0x15, op=Ops.ADD)
    print("pre-copy op1:", op1)
    op2 = copy.deepcopy(op1)
    op2.set_name("op2")
    print("copy of op1: ", op2)
    print("1op == op2:", op1 == op2)
    op1.randomize()
    print("randomized op1:", op1)


@cocotb.test()
async def alu_result(dut):
    """Exercise the ALUResult Transaction"""
    result = AluResult("result", 0x0FFD)
    print(result)
    result2 = copy.deepcopy(result)
    result2.set_name("result2")
    print(result2)
    print("Same?", result == result2)
    assert True
