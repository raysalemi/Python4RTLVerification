from cocotb.triggers import FallingEdge
from cocotb.result import TestFailure, TestSuccess
import cocotb
from tinyalu_utils import TinyAluBfm


@cocotb.test()
async def test_alu(dut):
    bfm = TinyAluBfm(dut)
    await bfm.startup_bfms()
    await FallingEdge(dut.clk)
    await bfm.send_op(0xAA, 0x55, 1)
    await cocotb.triggers.ClockCycles(dut.clk, 10)
    cmd = await bfm.get_cmd()
    result = await bfm.get_result()
    print("cmd:", cmd)
    print("result:", result)
    if result != 0xFF:
        raise TestFailure(f"ERROR: Bad answer {result:x} should be 0xFF")
    else:
        raise TestSuccess
