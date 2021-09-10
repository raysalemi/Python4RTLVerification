import cocotb
from cocotb.triggers import ClockCycles, FallingEdge


@cocotb.test()
async def no_count(dut):
    """Test no count if reset is 0"""
    dut.reset_n = 0
    await ClockCycles(dut.clk, 5)
    count = dut.count.value
    print("After 5 clocks count is ", count)
    assert count == 0


@cocotb.test()
async def three_count(dut):
    """Test that we count up as expected"""
    dut.reset_n = 0
    await FallingEdge(dut.clk)
    dut.reset_n = 1
    wait_3 = ClockCycles(dut.clk, 3, rising=False)
    await wait_3
    count = int(dut.count.value)
    print("After 3 clocks, count is ", count)
    assert count == 3


@cocotb.test()
async def oops(dut):
    """Demonstrate a coroutine mistake"""
    dut.reset_n = 0
    ClockCycles(dut.clk, 6)
    print("Did not await")
