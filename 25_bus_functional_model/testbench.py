import cocotb
import random
# All testbenches use tinyalu_utils, so store it in a central
# place and add its path to the sys path so we can import it
import sys
from pathlib import Path
sys.path.append(str(Path("..").resolve()))
from tinyalu_utils import TinyAluBfm, Ops, alu_prediction, logger  # noqa: E402


@cocotb.test()
async def test_alu(_):
    """Test all TinyALU Operations"""
    passed = True
    bfm = TinyAluBfm()
    await bfm.reset()
    await bfm.start_bfms()
    cvg = set()
    ops = list(Ops)
    for op in ops:
        aa = random.randint(0, 255)
        bb = random.randint(0, 255)
        await bfm.send_op(aa, bb, op)
        seen_cmd = await bfm.get_cmd()
        seen_op = Ops(seen_cmd[2])
        cvg.add(seen_op)
        result = await bfm.get_result()
        pr = alu_prediction(aa, bb, op)
        if result == pr:
            logger.info(f"PASSED: {aa} {op.name} {bb} = {result}")
        else:
            logger.error(f"FAILED: {aa} {op.name} {bb} = {result} - predicted {pr}")
            passed = False
    assert passed
