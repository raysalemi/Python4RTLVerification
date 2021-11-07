import cocotb
from pyuvm import *
import random
from pathlib import Path
import sys
# All testbenches use tinyalu_utils, so store it in a central
# place and add its path to the sys path so we can import it
sys.path.append(str(Path("..").resolve()))
from tinyalu_utils import TinyAluBfm, Ops, alu_prediction, logger  # noqa: E402


class RandomTester(uvm_component):

    def build_phase(self):
        self.bpp = uvm_blocking_put_port("bpp", self)

    async def until_done(self):
        await self.bpp.put((0, 0, Ops.ADD))
        await self.bpp.put((0, 0, Ops.ADD))
        await self.bpp.put((0, 0, Ops.ADD))
        await self.bpp.put((0, 0, Ops.ADD))

    async def run_phase(self):
        self.raise_objection()
        ops = list(Ops)
        for op in ops:
            aa = random.randint(0, 255)
            bb = random.randint(0, 255)
            await self.bpp.put((aa, bb, op))
        # send two dummy operations to allow
        # last real operation to complete
        await self.until_done()
        self.drop_objection()


class Driver(uvm_driver):

    def build_phase(self):
        self.bfm = ConfigDB().get(self, "", "BFM")
        self.bgp = uvm_blocking_get_port("bgp", self)

    async def run_phase(self):
        await self.bfm.reset()
        await self.bfm.start_bfms()
        while True:
            aa, bb, op = await self.bgp.get()
            self.logger.info(f"******* SENDING op: {(aa, op.name, bb)}")
            await self.bfm.send_op(aa, bb, op)
            self.logger.info(f"******* SENT op: {(aa, op.name, bb)}")


class MaxTester(RandomTester):

    async def run_phase(self):
        self.raise_objection()
        ops = list(Ops)
        for op in ops:
            aa = 0xFF
            bb = 0xFF
            await self.bpp.put((aa, bb, op))
        # send two dummy operations to allow
        # last real operation to complete
        await self.until_done()
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
            self.logger.info(f"***** GOT op: {cmd}")
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


class RandomAluEnv(uvm_env):
    """Instantiate the BFM and scoreboard"""

    def build_phase(self):
        dut = ConfigDB().get(self, "", "DUT")
        bfm = TinyAluBfm(dut)
        ConfigDB().set(None, "*", "BFM", bfm)
        self.driver = Driver("driver", self)
        self.tester = RandomTester("tester", self)
        self.cmd_fifo = uvm_tlm_fifo("cmd_fifo", self)
        self.scoreboard = Scoreboard("scoreboard", self)

    def connect_phase(self):
        self.tester.bpp.connect(self.cmd_fifo.put_export)
        self.driver.bgp.connect(self.cmd_fifo.get_export)


class MaxAluEnv(RandomAluEnv):
    """Generate maximum operands"""

    def build_phase(self):
        uvm_factory().set_type_override_by_type(RandomTester, MaxTester)
        super().build_phase()


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
    ConfigDB().set(None, "*", "DUT", dut)
    await uvm_root().run_test("RandomTest")


@cocotb.test()
async def max_test(dut):
    """Maximum operands"""
    ConfigDB().set(None, "*", "DUT", dut)
    await uvm_root().run_test("MaxTest")
