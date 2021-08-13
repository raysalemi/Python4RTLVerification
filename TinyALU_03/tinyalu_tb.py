from cocotb.triggers import FallingEdge
import cocotb
from cocotb.queue import QueueEmpty
from tinyalu_utils import TinyAluBfm, Ops, alu_prediction
import random
import logging


@cocotb.test()
async def test_alu(dut):
    passed = True
    logging.basicConfig(level=logging.NOTSET)
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)    
    bfm = TinyAluBfm(dut)
    await bfm.reset()
    cocotb.fork(bfm.driver_bfm())
    cocotb.fork(bfm.result_mon_bfm())
    cvg = set()
    ops = list(Ops)
    while True:
        aa = random.randint(0, 255)
        bb = random.randint(0, 255)
        op = ops.pop()
        cvg.add(op)
        await bfm.send_op(aa, bb, op)
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
    
