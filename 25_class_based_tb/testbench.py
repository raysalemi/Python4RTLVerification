import cocotb
import random
from pathlib import Path
import sys
# All testbenches use tinyalu_utils, so store it in a central
# place and add its path to the sys path so we can import it
sys.path.append(str(Path("..").resolve()))
from tinyalu_utils import TinyAluBfm, Ops, alu_prediction, logger  # noqa: E402


class Tester():
    def __init__(self, bfm):
        self.bfm = bfm

    async def execute(self):
        ops = list(Ops)
        for op in ops:
            aa = random.randint(0, 255)
            bb = random.randint(0, 255)
            await self.bfm.send_op(aa, bb, op)
        # send two dummy operations to allow
        # last real operation to complete
        await self.bfm.send_op(0, 0, 1)
        await self.bfm.send_op(0, 0, 1)


class Scoreboard():
    def __init__(self, bfm):
        self.bfm = bfm
        self.ops = []
        self.results = []
        self.cvg = set()

    async def get_cmds(self):
        while True:
            op = await self.bfm.get_cmd()
            self.ops.append(op)
            self.cvg.add(Ops(op[2]))

    async def get_results(self):
        while True:
            result = await self.bfm.get_result()
            self.results.append(result)

    async def execute(self):
        cocotb.fork(self.get_cmds())
        cocotb.fork(self.get_results())

    def check_results(self):
        passed = True
        for cmd in self.ops:
            (aa, bb, op) = cmd
            result = self.results.pop(0)
            pr = alu_prediction(aa, bb, Ops(op), error=False)
            if result == pr:
                logger.info(f"PASSED: {aa} {op} {bb} = {result}")
            else:
                passed = False
                logger.error(
                    f"FAILED: {aa} {op} {bb} = {result} - predicted {pr}")

        if len(set(Ops) - self.cvg) > 0:
            logger.error(
                f"Functional coverage error. Missed: {set(Ops)-self.cvg}")
            passed = False
        else:
            logger.info("Covered all operations")
        return passed


@cocotb.test()
async def test_alu(dut):
    bfm = TinyAluBfm(dut)
    tester = Tester(bfm)
    scoreboard = Scoreboard(bfm)
    await bfm.reset()
    await bfm.start_bfms()
    cocotb.fork(scoreboard.execute())
    await tester.execute()
    passed = scoreboard.check_results()
    assert passed
