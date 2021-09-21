import cocotb
import random
# All testbenches use tinyalu_utils, so store it in a central
# place and add its path to the sys path so we can import it
import sys
from pathlib import Path
sys.path.append(str(Path("..").resolve()))
from tinyalu_utils import TinyAluBfm, Ops, alu_prediction, logger  # noqa: E402


@cocotb.test()
async def test_alu(dut):
    """Test all TinyALU Operations"""
    passed = True
    bfm = TinyAluBfm(dut)
    await bfm.reset()
    await bfm.start_bfms()
    cvg = set()
    ops = list(Ops)
    while True:
        aa = random.randint(0, 255)
        bb = random.randint(0, 255)
        op = ops.pop()
        await bfm.send_op(aa, bb, op)
        seen_cmd = await bfm.get_cmd()
        seen_op = Ops(seen_cmd[2])
        cvg.add(seen_op)
        result = await bfm.get_result()
        result = int(dut.result.value)
        pr = alu_prediction(aa, bb, op, error=False)
        if result == pr:
            logger.info(f"PASSED: {aa} {op} {bb} = {result}")
        else:
            logger.error(f"FAILED: {aa} {op} {bb} = {result} - predicted {pr}")
            passed = False
        if len(ops) == 0:
            if len(set(Ops) - cvg) > 0:
                logger.error(f"Functional coverage error. Missed: {set(Ops)-cvg}")
            else:
                logger.info("Covered all operations")
            break
    assert passed
