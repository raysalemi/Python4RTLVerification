from cocotb.clock import Clock
from cocotb.triggers import FallingEdge, RisingEdge
import cocotb


@cocotb.test()
async def hello_world(dut):
    print("Hello, world.")

@cocotb.test(expect_fail=True)
async def failure(dut):
    assert False, "Oh, the humanity!"

async def reset(dut):
    await FallingEdge(dut.clk)
    dut.reset_n = 0
    dut.A = 0
    dut.B = 0
    dut.op = 0
    await FallingEdge(dut.clk)
    dut.reset_n = 1


@cocotb.test(expect_fail=False)
async def test_alu(dut):
    clock = Clock(dut.clk, 2, units="us")
    cocotb.fork(clock.start())
    await reset(dut)
    await FallingEdge(dut.clk)
    dut.A = 1
    dut.B = 2
    dut.op = 1 #add
    dut.start = 1
    await RisingEdge(dut.done)
    await FallingEdge(dut.clk)
    assert dut.result == 3, "Tinyalu Addition Failure"
    print("TinyALU Passed")



