# ## Importing modules

# Figure 3: Importing needed resources
import cocotb
from cocotb.triggers import FallingEdge
import random

# ### The tinyalu_utils module

# All testbenches use tinyalu_utils, so store it in a central
# place and add its path to the sys path so we can import it

from pathlib import Path
parent_path = Path("..").resolve()

import sys  # noqa: E402
sys.path.insert(0, str(parent_path))

from tinyalu_utils import Ops, alu_prediction, logger, get_int  # noqa: E402


# ## Setting up the cocotb TinyALU test

# Figure 7: The start of the TinyALU. Reset the DUT
@cocotb.test()
async def alu_test(dut):
    passed = True
    cvg = set()  # functional coverage
    await FallingEdge(dut.clk)
    dut.reset_n.value = 0
    dut.start.value = 0
    await FallingEdge(dut.clk)
    dut.reset_n.value = 1
# ### Sending commands
# Figure 8: Creating one transaction for each operation
    cmd_count = 1
    op_list = list(Ops)
    num_ops = len(op_list)
    while cmd_count <= num_ops:
        await FallingEdge(dut.clk)
        st = get_int(dut.start)
        dn = get_int(dut.done)
# ### Sending a command and waiting for it to complete
# Figure 9: Creating a TinyALU command
        if st == 0 and dn == 0:
            aa = random.randint(0, 255)
            bb = random.randint(0, 255)
            op = op_list.pop(0)
            cvg.add(op)
            dut.A.value = aa
            dut.B.value = bb
            dut.op.value = op
            dut.start.value = 1
# Figure 10: Asserting that a failure state never happens
        if st == 0 and dn == 1:
            raise AssertionError("DUT Error: done set to 1 without start")
# Figure 11: If we are in an operation, continue
        if st == 1 and dn == 0:
            continue
# ### Checking the result
# Figure 12: The operation is complete
        if st == 1 and dn == 1:
            dut.start.value = 0
            cmd_count += 1
            result = get_int(dut.result)
# Figure 13: Checking results against the prediction
            pr = alu_prediction(aa, bb, op)
            if result == pr:
                logger.info(
                    f"PASSED: {aa:2x} {op.name} {bb:2x} = {result:04x}")
            else:
                logger.error(
                    f"FAILED: {aa:2x} {op.name} {bb:2x} ="
                    f" {result:04x} - predicted {pr:04x}")
                passed = False
# ### Finishing the test
# Figure 14: Checking functional coverage using a set
    if len(set(Ops) - cvg) > 0:
        logger.error(f"Functional coverage error. Missed: {set(Ops)-cvg}")
        passed = False
    else:
        logger.info("Covered all operations")
# Figure 15: This assertion relays pass/fail to cocotb
    assert passed
