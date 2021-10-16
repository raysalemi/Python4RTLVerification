import cocotb
from cocotb.triggers import FallingEdge
import random
# All testbenches use tinyalu_utils, so store it in a central
# place and add its path to the sys path so we can import it
import sys
from pathlib import Path
sys.path.append(str(Path("..").resolve()))
from tinyalu_utils import Ops, alu_prediction, logger, get_int  # noqa: E402


@cocotb.test()
async def alu_test(dut):
    passed = True
    cvg = set()  # functional coverage
    await FallingEdge(dut.clk)
    dut.reset_n <= 0
    dut.start <= 0
    await FallingEdge(dut.clk)
    dut.reset_n <= 1
    cmd_count = 1
    while cmd_count <= 4:
        await FallingEdge(dut.clk)
        st = get_int(dut.start)
        dn = get_int(dut.done)
        if st == 0 and dn == 0:
            aa = random.randint(0, 255)
            bb = random.randint(0, 255)
            op = random.choice(list(Ops))
            cvg.add(op)
            dut.A <= aa
            dut.B <= bb
            dut.op <= op
            dut.start <= 1
        if st == 1 and dn == 0 or st == 0 and dn == 1:
            continue
        if st == 1 and dn == 1:
            dut.start <= 0
            cmd_count += 1
            result = get_int(dut.result)
            pr = alu_prediction(aa, bb, op)
            if result == pr:
                logger.info(f"PASSED: {aa} {op.name} {bb} = {result}")
            else:
                logger.error(f"FAILED: {aa} {op.name} {bb} = {result} - predicted {pr}")
                passed = False
    if len(set(Ops) - cvg) > 0:
        logger.error(f"Functional coverage error. Missed: {set(Ops)-cvg}")
        passed = False
    else:
        logger.info("Covered all operations")
    assert passed
