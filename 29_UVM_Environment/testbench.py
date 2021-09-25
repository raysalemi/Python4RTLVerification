import cocotb
from pyuvm import *
import random
# All testbenches use tinyalu_utils, so store it in a central
# place and add its path to the sys path so we can import it
import sys
from pathlib import Path
sys.path.append(str(Path("..").resolve()))
from tinyalu_utils import TinyAluBfm, Ops, alu_prediction  # noqa: E402


class BaseEnv(uvm_env):
    async def set_up_sim(self):
        cocotb.fork(self.bfm.driver_bfm())
        cocotb.fork(self.bfm.result_mon_bfm())
        cocotb.fork(self.bfm.cmd_mon_bfm())
        await self.bfm.reset()

    def build_phase(self):
        self.bfm = ConfigDB().get(self, "", "BFM")

    def end_of_elaboration_phase(self):
        self.cvg = set()

    def extract_phase(self):
        self.missed_ops = set(Ops) - self.cvg

    def check_phase(self):
        if len(self.missed_ops) > 0:
            self.logger.warning(f"Functional coverage error. Missed: {set(Ops)-self.cvg}")


class RandomEnv(BaseEnv):
    async def run_phase(self):
        self.raise_objection()
        await self.set_up_sim()
        for op in list(Ops):
            A = random.randrange(256)
            B = random.randrange(256)
            self.cvg.add(op)
            predicted_result = alu_prediction(A, B, op)
            await self.bfm.send_op(A, B, int(op))
            actual_result = await self.bfm.get_result()
            if predicted_result == actual_result:
                self.logger.info(f"PASSED: {A:02x} {op.name} {B:02x} = {actual_result:04x}")
            else:
                self.logger.error(f"FAILED: {A:02x} {op.name} {B:02x} = {actual_result:04x} expected {predicted_result:04x}")
        self.drop_objection()  # drop the objection to end


class MaxEnv(BaseEnv):
    async def run_phase(self):
        self.raise_objection()
        await self.set_up_sim()
        A = 0xFF
        B = 0xFF
        for op in list(Ops):
            self.cvg.add(op)
            predicted_result = alu_prediction(A, B, op)
            await self.bfm.send_op(A, B, int(op))
            actual_result = await self.bfm.get_result()
            if predicted_result == actual_result:
                self.logger.info(f"PASSED: {A:02x} {op.name} {B:02x} = {actual_result:04x}")
            else:
                self.logger.error(f"FAILED: {A:02x} {op.name} {B:02x} = {actual_result:04x} expected {predicted_result:04x}")
        self.drop_objection()


class RandomTest(uvm_test):
    def build_phase(self):
        self.env = RandomEnv("env", self)


class MaxTest(uvm_test):
    def build_phase(self):
        self.env = MaxEnv("env", self)


@cocotb.test()
async def random_env(dut):
    """
    Demonstrates using an environment
    """
    bfm = TinyAluBfm(dut)
    ConfigDB().set(None, "*", "BFM", bfm)
    await uvm_root().run_test("RandomTest")
    assert True


@cocotb.test()
async def max_env(dut):
    """
    Demonstrates using an environment to run a different test
    """
    bfm = TinyAluBfm(dut)
    await bfm.start_bfms()
    ConfigDB().set(None, "*", "BFM", bfm)
    await uvm_root().run_test("MaxTest")
    assert True
