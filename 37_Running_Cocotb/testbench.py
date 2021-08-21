import cocotb


@cocotb.test()
async def hello_world(dut):
    print("*" * 24)
    print("****  Hello, world. ****")
    print("*" * 24)
