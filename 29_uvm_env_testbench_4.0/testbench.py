import cocotb
from pyuvm import *
import random
from pathlib import Path
import sys
# All testbenches use tinyalu_utils, so store it in a central
# place and add its path to the sys path so we can import it
sys.path.append(str(Path("..").resolve()))
from tinyalu_utils import TinyAluBfm, Ops, alu_prediction, logger  # noqa: E402


class BaseTester(uvm_component):

    def start_of_simulation_phase(self):
        TinyAluBfm().start_tasks()

    async def run_phase(self):
        self.raise_objection()
        self.bfm = TinyAluBfm()
        ops = list(Ops)
        for op in ops:
            aa, bb = self.get_operands()
            await self.bfm.send_op(aa, bb, op)
        # send two dummy operations to allow
        # last real operation to complete
        await self.bfm.send_op(0, 0, 1)
        await self.bfm.send_op(0, 0, 1)
        self.drop_objection()


class RandomTester(BaseTester):
    def get_operands(self):
        return random.randint(0, 255), random.randint(0, 255)


class MaxTester(BaseTester):
    def get_operands(self):
        return 0xFF, 0xFF


class Scoreboard(uvm_component):

    async def get_cmds(self):
        while True:
            cmd = await self.bfm.get_cmd()
            self.cmds.append(cmd)

    async def get_results(self):
        while True:
            result = await self.bfm.get_result()
            self.results.append(result)

    def start_of_simulation_phase(self):
        self.bfm = TinyAluBfm()
        self.cmds = []
        self.results = []
        self.cvg = set()
        cocotb.start_soon(self.get_cmds())
        cocotb.start_soon(self.get_results())

    def check_phase(self):
        passed = True
        for cmd in self.cmds:
            aa, bb, op_int = cmd
            op = Ops(op_int)
            self.cvg.add(op)
            actual = self.results.pop(0)
            prediction = alu_prediction(aa, bb, op)
            if actual == prediction:
                logger.info(
                    f"PASSED: {aa:02x} {op.name} {bb:02x} = {actual:04x}")
            else:
                passed = False
                logger.error(
                    f"FAILED: {aa:02x} {op.name} {bb:02x} = {actual:04x}"
                    f" - predicted {prediction:04x}")

        if len(set(Ops) - self.cvg) > 0:
            logger.error(
                f"Functional coverage error. Missed: {set(Ops)-self.cvg}")
            passed = False
        else:
            logger.info("Covered all operations")
        assert passed


class BaseAluEnv(uvm_env):
    """Instantiate the BFM and scoreboard"""

    def build_phase(self):
        self.scoreboard = Scoreboard("scoreboard", self)


class RandomAluEnv(BaseAluEnv):
    """Generate random operands"""

    def build_phase(self):
        super().build_phase()
        self.tester = RandomTester("tester", self)


class MaxAluEnv(BaseAluEnv):
    """Generate maximum operands"""

    def build_phase(self):
        super().build_phase()
        self.tester = MaxTester("tester", self)


class RandomTest(uvm_test):
    """Run with random operands"""
    def build_phase(self):
        self.env = RandomAluEnv("env", self)


class MaxTest(uvm_test):
    """Run with max operands"""
    def build_phase(self):
        self.env = MaxAluEnv("env", self)


@cocotb.test()
async def random_test(dut):
    """Random operands"""
    await uvm_root().run_test(RandomTest)


@cocotb.test()
async def max_test(dut):
    """Maximum operands"""
    await uvm_root().run_test(MaxTest)
