import cocotb
from cocotb.triggers import Timer


@cocotb.test()
async def wait_2ns(dut):
    """Waits for two ns then prints"""
    await Timer(2, units="ns")
    print("I am DONE waiting!")


@cocotb.test()
async def hello_world(dut):
    """Say hello!"""
    print("Hello, world.")
