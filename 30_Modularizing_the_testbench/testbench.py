import cocotb
from pyuvm import *
import random
# All testbenches use tinyalu_utils, so store it in a central
# place and add its path to the sys path so we can import it
import sys
from pathlib import Path
sys.path.append(str(Path("..").resolve()))
from tinyalu_utils import TinyAluBfm, Ops, alu_prediction  # noqa: E402


class Coverage(uvm_component):

    def end_of_elaboration_phase(self):
        self.cvg = set()

    def write(self, op):
        assert isinstance(op, Ops), "Coverage can only receive Ops"
        self.cvg.add(op)

    def check_phase(self):
        if len(set(Ops) - self.cvg) > 0:
            self.logger.error(f"Functional coverage error. Missed: {set(Ops)-self.cvg}")
        else:
            self.logger.info("All functions covered")


class Scoreboard(uvm_component):

    def end_of_elaboration_phase(self):
        self.results = []

    def write(self, op_result):
        A, B, op, actual_result = op_result
        predicted_result = alu_prediction(A, B, op)
        self.results.append((A, B, op, predicted_result, actual_result))

    def check_phase(self):
        for A, B, op, predicted_result, actual_result in self.results:
            if predicted_result == actual_result:
                self.logger.info(f"PASSED: {A:02x} {op.name} {B:02x} ="
                                 f" {actual_result:04x}")
            else:
                self.logger.error(f"FAILED: {A:02x} {op.name} {B:02x} ="
                                  f" {actual_result:04x} expected {predicted_result:04x}")


class AluEnv(uvm_env):
    async def set_up_sim(self):
        cocotb.fork(self.bfm.driver_bfm())
        cocotb.fork(self.bfm.result_mon_bfm())
        cocotb.fork(self.bfm.cmd_mon_bfm())
        await self.bfm.reset()

    def build_phase(self):
        self.cvg = Coverage("cvg", self)
        self.scb = Scoreboard("scb", self)
        self.bfm = ConfigDB().get(self, "", "BFM")

    async def run_phase(self):
        self.raise_objection()  # You MUST raise an objection
        await self.set_up_sim()
        for op in list(Ops):
            A = random.randrange(256)
            B = random.randrange(256)
            await self.bfm.send_op(A, B, int(op))
            actual_result = await self.bfm.get_result()
            result_tuple = (A, B, op, actual_result)
            self.scb.write(result_tuple)
            self.cvg.write(op)
        self.drop_objection()  # drop the objection to end


class AluTest(uvm_test):
    def build_phase(self):
        self.env = AluEnv("env", self)


@cocotb.test()
async def modular(dut):
    """
    Demonstrates using components to modularize the testbench
    """
    bfm = TinyAluBfm(dut)
    await bfm.startup_bfms()
    ConfigDB().set(None, "*", "BFM", bfm)
    await uvm_root().run_test("AluTest")
    assert True
