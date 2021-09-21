import cocotb
from pyuvm import *
import random
# All testbenches use tinyalu_utils, so store it in a central
# place and add its path to the sys path so we can import it
import sys
from pathlib import Path
sys.path.append(str(Path("..").resolve()))
from tinyalu_utils import TinyAluBfm, Ops, alu_prediction  # noqa: E402


class HelloWorldTest(uvm_test):
    async def run_phase(self):
        self.raise_objection()
        self.logger.info("Hello, world.")
        self.drop_objection()


class AluTest(uvm_test):

    def build_phase(self):
        self.bfm = ConfigDB().get(self, "", "BFM")

    async def run_phase(self):
        self.raise_objection()   # You MUST raise an objection
        passed = True
        cvg = set()  # functional coverage
        for op in list(Ops):
            A = random.randrange(256)
            B = random.randrange(256)
            cvg.add(op)
            predicted_result = alu_prediction(A, B, op, error=False)
            await self.bfm.send_op(A, B, int(op))
            actual_result = await self.bfm.get_result()
            if predicted_result == actual_result:
                self.logger.info(
                    f"PASSED: {A:02x} {op.name} {B:02x} = {actual_result:04x}")
            else:
                self.logger.error(
                    f"FAILED: {A:02x} {op.name} {B:02x} = "
                    f"{actual_result:04x} expected {predicted_result:04x}")
                passed = False
        if len(set(Ops) - cvg) > 0:
            self.logger.error(
                f"Functional coverage error. Missed: {set(Ops)-cvg}")
            passed = False
        else:
            self.logger.info("Covered all operations")
        assert passed
        self.drop_objection()  # drop the objection to end


@cocotb.test()
async def hello_test(dut):
    """
    Show a simple Hello World Test
    """
    await uvm_root().run_test("HelloWorldTest")


@cocotb.test()
async def alu_test(dut):
    """
    Run ALU test
    """
    bfm = TinyAluBfm(dut)
    await bfm.startup_bfms()
    ConfigDB().set(None, "*", "BFM", bfm)
    await uvm_root().run_test("AluTest")
