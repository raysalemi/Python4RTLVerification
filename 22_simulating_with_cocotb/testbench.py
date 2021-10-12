import cocotb
from cocotb.triggers import ClockCycles, FallingEdge
from pathlib import Path
import logging
import sys
# All testbenches use tinyalu_utils, so store it in a central
# place and add its path to the sys path so we can import it
sys.path.append(str(Path("..").resolve()))
from tinyalu_utils import get_int  # noqa: E402

logging.basicConfig(level=logging.NOTSET)
logger = logging.getLogger()
logger.setLevel(logging.INFO)


@cocotb.test()
async def no_count(dut):
    """Test no count if reset is 0"""
    dut.reset_n = 0
    await ClockCycles(dut.clk, 5)
    count = get_int(dut.count)
    logger.info(f"After 5 clocks count is {count}")
    assert count == 0


@cocotb.test()
async def three_count(dut):
    """Test that we count up as expected"""
    dut.reset_n = 0
    await FallingEdge(dut.clk)
    dut.reset_n = 1
    await ClockCycles(dut.clk, 3, rising=False)
    count = get_int(dut.count)
    logger.info(f"After 3 clocks, count is {count}")
    assert count == 3


@cocotb.test()
async def oops(dut):
    """Demonstrate a coroutine mistake"""
    dut.reset_n = 0
    ClockCycles(dut.clk, 6)
    logger.info("Did not await")
