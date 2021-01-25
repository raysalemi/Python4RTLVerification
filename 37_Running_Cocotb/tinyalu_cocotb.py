from cocotb.clock import Clock
from cocotb.triggers import FallingEdge, RisingEdge
import cocotb


@cocotb.test()
async def hello_world(dut):
    print("Hello, world.")




