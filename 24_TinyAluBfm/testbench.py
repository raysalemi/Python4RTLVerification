import cocotb
import random
# All testbenches use tinyalu_utils, so store it in a central
# place and add its path to the sys path so we can import it
import sys
from pathlib import Path
sys.path.insert(0, str(Path("..").resolve()))
from tinyalu_utils import TinyAluBfm, Ops, alu_prediction, logger  # noqa: E402


# ## The cocotb test
# Figure 15: Starting a test by resetting the DUT
# and starting the BFM tasks
@cocotb.test()
async def test_alu(_):
    """Test all TinyALU Operations"""
    passed = True
    bfm = TinyAluBfm()
    await bfm.reset()
    bfm.start_tasks()
# ### Sending commands
    cvg = set()
# Figure 16: Creating a command and sending it
    ops = list(Ops)
    for op in ops:
        aa = random.randint(0, 255)
        bb = random.randint(0, 255)
        await bfm.send_op(aa, bb, op)
# ### Monitoring commands
# Figure 17: Wait to get the command from the DUT
# and store it in the coverage set
        seen_cmd = await bfm.get_cmd()
        seen_op = Ops(seen_cmd[2])
        cvg.add(seen_op)
# Figure 18: Wait for the result, then create a prediction
        result = await bfm.get_result()
        pr = alu_prediction(aa, bb, op)
# Figure 19: Check the result against the predicted result
        if result == pr:
            logger.info(f"PASSED: {aa:02x} {op.name} {bb:02x} = {result:04x}")
        else:
            logger.error(f"FAILED: {aa:02x} {op.name} {bb:02x} = "
                         f"{result:04x} - predicted {pr:04x}")
            passed = False

    if len(set(Ops) - cvg) > 0:
        logger.error(f"Functional coverage error. Missed: {set(Ops)-cvg}")
        passed = False
    else:
        logger.info("Covered all operations")
# Figure 20: Assert that we passed to pass to cocotb
    assert passed
