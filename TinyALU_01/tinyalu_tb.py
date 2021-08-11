import cocotb
from cocotb.triggers import ClockCycles, FallingEdge, RisingEdge
import enum
import random
import logging


@enum.unique
class Ops(enum.IntEnum):
    """Legal ops for the TinyALU"""
    ADD = 1
    AND = 2
    XOR = 3
    MUL = 4


def alu_prediction(A, B, op, error = False):
    """Python model of the TinyALU"""
    assert isinstance(op, Ops), "The tinyalu op must be of type ops"
    if op == Ops.ADD:
        result = A + B
    elif op == Ops.AND:
        result = A & B
    elif op == Ops.XOR:
        result = A ^ B
    elif op == Ops.MUL:
        result = A * B
    if error and (random.randint(0,3) == 0):
        result = result + 1
    return result


@cocotb.test()
async def alu_test(dut):
    logging.basicConfig(level=logging.NOTSET)
    logger = logging.getLogger()
    cvg = set() #functional coverage
    await FallingEdge(dut.clk)
    dut.reset_n = 0
    await FallingEdge(dut.clk)
    dut.reset_n = 1

    for _ in range(3):

        aa = random.randrange(256)
        bb = random.randrange(256)
        op = random.choice(list(Ops))
        cvg.add(op)
        dut.A = aa
        dut.B = bb
        dut.op = int(op)
        dut.start = 1
        await FallingEdge(dut.clk)
        await RisingEdge(dut.done)
        actual_result = int(dut.result.value)
        dut.start = 0
        predicted_result = alu_prediction(aa, bb, op, error = True)
        if predicted_result == actual_result:
            logger.info (f"PASSED:  {aa:02x} {op.name} {bb:02x} = {actual_result:04x}")
        else:
            logger.error (f"FAILED: {aa:02x} {op.name} {bb:02x} = {actual_result:04x} expected {predicted_result:04x}")
    if len(set(Ops) - cvg) > 0:
        logger.error(f"Functional coverage error. Missed: {set(Ops)-cvg}")