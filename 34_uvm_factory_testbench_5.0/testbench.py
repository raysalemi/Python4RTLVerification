import cocotb
import pyuvm
from pyuvm import *
import random
from pathlib import Path
import sys
# All testbenches use tinyalu_utils, so store it in a central
# place and add its path to the sys path so we can import it
sys.path.insert(0, str(Path("..").resolve()))
from tinyalu_utils import TinyAluBfm, Ops, alu_prediction  # noqa: E402


# # UVM Factory testbench 5.0
# ### BaseTester
# Figure 2: Abstract base class raises an error if instantiated
class BaseTester(uvm_component):

    def get_operands(self):
        raise RuntimeError("You must extend BaseTester and override get_operands().")

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


# ### RandomTester and MaxTester
class RandomTester(BaseTester):
    def get_operands(self):
        return random.randint(0, 255), random.randint(0, 255)


class MaxTester(BaseTester):
    def get_operands(self):
        return 0xFF, 0xFF


# ### Scoreboard
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
                self.logger.info(
                    f"PASSED: {aa:02x} {op.name} {bb:02x} = {actual:04x}")
            else:
                passed = False
                self.logger.error(
                    f"FAILED: {aa:02x} {op.name} {bb:02x} = {actual:04x}"
                    f" - predicted {prediction:04x}")

        if len(set(Ops) - self.cvg) > 0:
            self.logger.error(
                f"Functional coverage error. Missed: {set(Ops)-self.cvg}")
            passed = False
        else:
            self.logger.info("Covered all operations")
        assert passed


# ## AluEnv
# Figure 1: Using the factory to instantiate the BaseTester
class AluEnv(uvm_env):
    """Instantiate the scoreboard"""

    def build_phase(self):
        self.scoreboard = Scoreboard("scoreboard", self)
        self.tester = BaseTester.create("tester", self)

    def start_of_simulation_phase(self):
        TinyAluBfm().start_tasks()


# ## RandomTest
# Figure 3: Overriding BaseTester with RandomTester
@pyuvm.test()
class RandomTest(uvm_test):
    """Run with random operands"""
    def build_phase(self):
        uvm_factory().set_type_override_by_type(BaseTester, RandomTester)
        self.env = AluEnv("env", self)


# ## MaxTest
# Figure 4: Overriding BaseTester with MaxTester
@pyuvm.test()
class MaxTest(uvm_test):
    """Run with max operands"""
    def build_phase(self):
        uvm_factory().set_type_override_by_type(BaseTester, MaxTester)
        self.env = AluEnv("env", self)
