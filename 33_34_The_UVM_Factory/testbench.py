import cocotb
from pyuvm import *
import random
from pathlib import Path
import sys
# All testbenches use tinyalu_utils, so store it in a central
# place and add its path to the sys path so we can import it
sys.path.append(str(Path("..").resolve()))
from tinyalu_utils import TinyAluBfm, Ops, alu_prediction, logger  # noqa: E402


class TinyComponent(uvm_component):
    async def run_phase(self):
        self.raise_objection()
        self.logger.info("I'm so tiny!")
        self.drop_objection()


class TinyTest(uvm_test):
    def build_phase(self):
        self.tc = TinyComponent("tc", self)


@cocotb.test()
async def tiny_test(_):
    await uvm_root().run_test("TinyTest")


class TinyFactoryTest(uvm_test):
    def build_phase(self):
        self.tc = TinyComponent.create("tc", self)


@cocotb.test()
async def tiny_factory_test(_):
    await uvm_root().run_test("TinyFactoryTest")


class MediumComponent(uvm_component):
    async def run_phase(self):
        self.raise_objection()
        self.logger.info("I'm medium size.")
        self.drop_objection()


class MediumFactoryTest(TinyFactoryTest):
    def build_phase(self):
        uvm_factory().set_type_override_by_type(
            TinyComponent, MediumComponent)
        super().build_phase()


@cocotb.test()
async def medium_factory_test(_):
    await uvm_root().run_test("MediumFactoryTest")


class MediumNameTest(TinyFactoryTest):
    def build_phase(self):
        uvm_factory().set_type_override_by_name(
            "TinyComponent", "MediumComponent")
        super().build_phase()

    def report_phase(self):
        uvm_factory().debug_level = 0
        uvm_factory_str = str(uvm_factory())
        self.logger.info(uvm_factory_str)


@cocotb.test()
async def medium_name_test(_):
    await uvm_root().run_test("MediumNameTest")


class TwoCompEnv(uvm_env):
    def build_phase(self):
        self.tc1 = TinyComponent.create("tc1", self)
        self.tc2 = TinyComponent.create("tc2", self)


class TwoCompTest(uvm_test):
    def build_phase(self):
        uvm_factory().set_inst_override_by_type(
            TinyComponent, MediumComponent, "uvm_test_top.env.tc1")
        self.env = TwoCompEnv("env", self)


@cocotb.test()
async def two_comp_test(_):
    uvm_factory().clear_overrides()
    await uvm_root().run_test("TwoCompTest")
    uvm_factory().print(0)


class CreateTest(uvm_test):
    def build_phase(self):
        self.tc = uvm_factory().create_component_by_name(
            "TinyComponent",
            name="tc", parent=self)


@cocotb.test()
async def create_test(_):
    """Create a component using factory"""
    uvm_factory().clear_overrides()
    await uvm_root().run_test("CreateTest")


class Tester(uvm_component):

    def build_phase(self):
        self.bfm = ConfigDB().get(self, "", "BFM")

    async def run_phase(self):
        self.raise_objection()
        await self.bfm.reset()
        await self.bfm.start_bfms()
        ops = list(Ops)
        for op in ops:
            aa = random.randint(0, 255)
            bb = random.randint(0, 255)
            await self.bfm.send_op(aa, bb, op)
        # send two dummy operations to allow
        # last real operation to complete
        await self.bfm.send_op(0, 0, 1)
        await self.bfm.send_op(0, 0, 1)
        self.drop_objection()


class MaxTester(Tester):

    async def run_phase(self):
        self.raise_objection()
        await self.bfm.reset()
        await self.bfm.start_bfms()
        ops = list(Ops)
        for op in ops:
            aa = 0xFF
            bb = 0xFF
            await self.bfm.send_op(aa, bb, op)
        # send two dummy operations to allow
        # last real operation to complete
        await self.bfm.send_op(0, 0, 1)
        await self.bfm.send_op(0, 0, 1)
        self.drop_objection()


class Scoreboard(uvm_component):

    def build_phase(self):
        self.bfm = ConfigDB().get(self, "", "BFM")
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

    async def run_phase(self):
        cocotb.fork(self.get_cmds())
        cocotb.fork(self.get_results())

    def check_phase(self):
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
                    f"FAILED: {aa} {Ops(op).name} {bb} = {actual} - predicted {prediction}")

        if len(set(Ops) - self.cvg) > 0:
            logger.error(
                f"Functional coverage error. Missed: {set(Ops)-self.cvg}")
            passed = False
        else:
            logger.info("Covered all operations")
        assert passed


class AluEnv(uvm_env):
    """Instantiate the BFM and scoreboard"""

    def build_phase(self):
        self.tester = Tester.create("tester", self)
        dut = ConfigDB().get(self, "", "DUT")
        bfm = TinyAluBfm(dut)
        ConfigDB().set(None, "*", "BFM", bfm)
        self.scoreboard = Scoreboard("scoreboard", self)


class RandomTest(uvm_test):
    """Run with random operands"""
    def build_phase(self):
        self.env = AluEnv("env", self)


class MaxTest(uvm_test):
    """Run with max operands"""
    def build_phase(self):
        uvm_factory().set_type_override_by_type(Tester, MaxTester)
        self.env = AluEnv("env", self)


@cocotb.test()
async def random_test(dut):
    """Random operands"""
    ConfigDB().set(None, "*", "DUT", dut)
    await uvm_root().run_test("RandomTest")


@cocotb.test()
async def max_test(dut):
    """Maximum operands"""
    ConfigDB().clear()
    ConfigDB().set(None, "*", "DUT", dut)
    await uvm_root().run_test("MaxTest")
