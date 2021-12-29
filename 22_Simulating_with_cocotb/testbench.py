import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles, FallingEdge
from pathlib import Path
import sys
# All testbenches use tinyalu_utils, so store it in a central
# place and add its path to the sys path so we can import it
sys.path.append(str(Path("..").resolve()))
from tinyalu_utils import get_int, logger  # noqa: E402


# ## Testing reset_n

@cocotb.test()
async def no_count(dut):
    """Test no count if reset is 0"""
    cocotb.start_soon(Clock(dut.clk, 2, units="ns").start())
    dut.reset_n.value = 0
    await ClockCycles(dut.clk, 5)
    count = get_int(dut.count.value)
    logger.info(f"After 5 clocks count is {count}")
    assert count == 0


# ## Checking that the counter counts
@cocotb.test()
async def three_count(dut):
    """Test that we count up as expected"""
    cocotb.start_soon(Clock(dut.clk, 2, units="ns").start())
    dut.reset_n.value = 0
    await FallingEdge(dut.clk)
    dut.reset_n.value = 1
    await ClockCycles(dut.clk, 3, rising=False)
    count = get_int(dut.count)
    logger.info(f"After 3 clocks, count is {count}")
    assert count == 3


# ## A common coroutine mistake

@cocotb.test()
async def oops(dut):
    """Demonstrate a coroutine mistake"""
    cocotb.start_soon(Clock(dut.clk, 2, units="ns").start())
    dut.reset_n.value = 0
    ClockCycles(dut.clk, 6)
    logger.info("Did not await")
