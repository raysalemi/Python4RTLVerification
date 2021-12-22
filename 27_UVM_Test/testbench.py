import cocotb
from pyuvm import *
import random
from pathlib import Path
import sys
# All testbenches use tinyalu_utils, so store it in a central
# place and add its path to the sys path so we can import it
sys.path.append(str(Path("..").resolve()))
from tinyalu_utils import TinyAluBfm, Ops, alu_prediction, logger  # noqa: E402


class HelloWorldTest(uvm_test):
    async def run_phase(self):
        self.raise_objection()
        self.logger.info("Hello, world.")
        self.drop_objection()


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


class MaxTester(Tester):

    async def execute(self):
        ops = list(Ops)
        for op in ops:
            aa = 0xFF
            bb = 0xFF
            await self.bfm.send_op(aa, bb, op)
        # send two dummy operations to allow
        # last real operation to complete
        await self.bfm.send_op(0, 0, 1)
        await self.bfm.send_op(0, 0, 1)


class Scoreboard():
    def __init__(self, bfm):
        self.bfm = bfm
        self.cmds = []
        self.results = []
        self.cvg = set()

    async def get_cmds(self):
        while True:
            cmd = await self.bfm.get_cmd()
            self.cmds.append(cmd)

    async def get_results(self):
        while True:
            result = await self.bfm.get_result()
            self.results.append(result)

    async def execute(self):
        cocotb.fork(self.get_cmds())
        cocotb.fork(self.get_results())

    def check_results(self):
        passed = True
        for cmd in self.cmds:
            (aa, bb, op) = cmd
            self.cvg.add(Ops(op))
            actual = self.results.pop(0)
            prediction = alu_prediction(aa, bb, Ops(op))
            if actual == prediction:
                logger.info(f"PASSED: {aa} {Ops(op).name} {bb} = {actual}")
            else:
                passed = False
                logger.error(
                    f"FAILED: {aa} {Ops(op).name}"
                    " {bb} = {actual} - predicted {prediction}")

        if len(set(Ops) - self.cvg) > 0:
            logger.error(
                f"Functional coverage error. Missed: {set(Ops)-self.cvg}")
            passed = False
        else:
            logger.info("Covered all operations")
        return passed


async def execute_test(TesterClass):
    bfm = TinyAluBfm()
    scoreboard = Scoreboard(bfm)
    await bfm.reset()
    bfm.start_tasks()
    cocotb.fork(scoreboard.execute())
    tester = TesterClass(bfm)
    await tester.execute()
    passed = scoreboard.check_results()
    return passed


class RandomTest(uvm_test):
    """Run with random operations"""
    async def run_phase(self):
        self.raise_objection()
        passed = await execute_test(Tester)
        assert passed
        self.drop_objection()


class MaxTest(uvm_test):
    """Run with random operations"""
    async def run_phase(self):
        self.raise_objection()
        passed = await execute_test(MaxTester)
        assert passed
        self.drop_objection()


@cocotb.test()
async def hello_world(_):
    """Say hello"""
    await uvm_root().run_test("HelloWorldTest")


@cocotb.test()
async def random_test(_):
    """Random operands"""
    await uvm_root().run_test("RandomTest")


@cocotb.test()
async def max_test(_):
    """Maximum operands"""
    await uvm_root().run_test("MaxTest")
