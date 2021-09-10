import cocotb
from cocotb.triggers import FallingEdge
import enum
import random
import logging


# Not used in the code, only the book
class Weapons(enum.Enum):
    SWORD = 'sword'
    BOW = 'bow'
    SPEAR = 'spear'


# Book example, not part of testbench
weapon = Weapons.SWORD
if weapon == Weapons.SWORD:
    damage = 3
elif weapon == Weapons.BOW:
    damage = 1
else:
    damage = 2

print(f"Damage {damage} from", weapon.value)
# end book example


class Ops(enum.IntEnum):
    """Legal ops for the TinyALU"""
    ADD = 1
    AND = 2
    XOR = 3
    MUL = 4


def alu_prediction(A, B, op, error=False):
    """Python model of the TinyALU"""
    assert isinstance(op, Ops), "The tinyalu op must be of type ops"
    if op == Ops.ADD:
        result = A + B
    elif op == Ops.AND:
        result = A & B
    elif op == Ops.XOR:
        result = A ^ B
    elif op == Ops.MUL:
        result = A * B
    if error and (random.randint(0, 3) == 0):
        result = result + 1
    return result


@cocotb.test()
async def alu_test(dut):
    passed = True
    logging.basicConfig(level=logging.NOTSET)
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    cvg = set()  # functional coverage
    await FallingEdge(dut.clk)
    dut.reset_n = 0
    dut.start = 0
    await FallingEdge(dut.clk)
    dut.reset_n = 1
    cmd_count = 1
    while cmd_count <= 6:
        await FallingEdge(dut.clk)
        st = int(dut.start.value)
        dn = int(dut.done.value)
        if st == 0 and dn == 0:
            aa = random.randint(0, 255)
            bb = random.randint(0, 255)
            op = random.choice(list(Ops))
            cvg.add(op)
            dut.A = aa
            dut.B = bb
            dut.op = op
            dut.start = 1
        if st == 1 and dn == 0 or st == 0 and dn == 1:
            continue
        if st == 1 and dn == 1:
            dut.start = 0
            cmd_count += 1
            result = int(dut.result.value)
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
