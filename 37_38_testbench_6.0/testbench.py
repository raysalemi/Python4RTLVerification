import cocotb
from pyuvm import *
import random
from pathlib import Path
import sys
# All testbenches use tinyalu_utils, so store it in a central
# place and add its path to the sys path so we can import it
sys.path.append(str(Path("..").resolve()))
from tinyalu_utils import TinyAluBfm, Ops, alu_prediction  # noqa: E402


class BaseTester(uvm_component):

    def get_operands(self):
        raise RuntimeError("You must extend BaseTester and override it.")

    def build_phase(self):
        self.pp = uvm_put_port("pp", self)

    async def run_phase(self):
        self.raise_objection()
        self.bfm = TinyAluBfm()
        ops = list(Ops)
        for op in ops:
            aa, bb = self.get_operands()
            cmd_tuple = (aa, bb, op)
            await self.pp.put(cmd_tuple)
        # send two dummy operations to allow
        # last real operation to complete
        await self.pp.put((0, 0, Ops.ADD))
        await self.pp.put((0, 0, Ops.ADD))
        await self.pp.put((0, 0, Ops.ADD))
        await self.pp.put((0, 0, Ops.ADD))
        self.drop_objection()


# ### RandomTester and MaxTester
class RandomTester(BaseTester):
    def get_operands(self):
        return random.randint(0, 255), random.randint(0, 255)


class MaxTester(BaseTester):
    def get_operands(self):
        return 0xFF, 0xFF


class Driver(uvm_driver):

    def build_phase(self):
        self.bfm = TinyAluBfm()
        self.gp = uvm_get_port("gp", self)

    async def run_phase(self):
        await self.bfm.reset()
        self.bfm.start_tasks()
        while True:
            aa, bb, op = await self.gp.get()
            await self.bfm.send_op(aa, bb, op)


class Monitor(uvm_monitor):
    def __init__(self, name, parent, method_name):
        super().__init__(name, parent)
        self.method_name = method_name

    def build_phase(self):
        self.ap = uvm_analysis_port("ap", self)
        self.bfm = TinyAluBfm()

    async def run_phase(self):
        while True:
            get_method = getattr(self.bfm, self.method_name)
            datum = await get_method()
            self.ap.write(datum)


class Coverage(uvm_analysis_export):
    def start_of_simulation_phase(self):
        self.cvg = set()

    def write(self, cmd):
        _, _, op = cmd
        self.cvg.add(Ops(op))

    def report_phase(self):
        if len(set(Ops) - self.cvg) > 0:
            self.logger.error(
                f"Functional coverage error. Missed: {set(Ops)-self.cvg}")
            assert False
        else:
            self.logger.info("Covered all operations")
            assert True


class Scoreboard(uvm_component):

    def build_phase(self):
        self.cmd_mon_fifo = uvm_tlm_analysis_fifo("cmd_mon_fifo", self)
        self.result_mon_fifo = uvm_tlm_analysis_fifo("result_mon_fifo", self)
        self.cmd_gp = uvm_get_port("cmd_gp", self)
        self.result_gp = uvm_get_port("result_gp", self)

    def connect_phase(self):
        self.cmd_export = self.cmd_mon_fifo.analysis_export
        self.result_export = self.result_mon_fifo.analysis_export
        self.cmd_gp.connect(self.cmd_mon_fifo.get_export)
        self.result_gp.connect(self.result_mon_fifo.get_export)

    def check_phase(self):
        passed = True
        while True:
            success, cmd = self.cmd_gp.try_get()
            if not success:
                break
            (aa, bb, op) = cmd
            prediction = alu_prediction(aa, bb, Ops(op))
            result_exists, actual = self.result_gp.try_get()
            if not result_exists:
                raise RuntimeError(f"Missing result for command {cmd}")
            if actual == prediction:
                self.logger.info(
                    f"PASSED: {aa:02x} {Ops(op).name} {bb:02x} = {actual:04x}")
            else:
                passed = False
                self.logger.error(
                    f"FAILED: {aa:02x} {Ops(op).name} {bb:02x} ="
                    f" {actual:04x} - predicted {prediction:04x}")
        assert passed


class Environment(uvm_env):
    """Instantiate the BFM and scoreboard"""

    def build_phase(self):
        self.tester = RandomTester.create("tester", self)
        self.driver = Driver("driver", self)
        self.cmd_fifo = uvm_tlm_fifo("cmd_fifo", self)
        self.scoreboard = Scoreboard("scoreboard", self)
        self.coverage = Coverage("coverage", self)
        self.cmd_mon = Monitor("cmd_monitor", self, "get_cmd")
        self.result_mon = Monitor("result_monitor", self, "get_result")

    def connect_phase(self):
        self.tester.pp.connect(self.cmd_fifo.put_export)
        self.driver.gp.connect(self.cmd_fifo.get_export)

        self.cmd_mon.ap.connect(self.coverage)
        self.cmd_mon.ap.connect(self.scoreboard.cmd_export)

        self.result_mon.ap.connect(self.scoreboard.result_export)


class RandomTest(uvm_test):
    """Run with random operands"""
    def build_phase(self):
        uvm_factory().set_type_override_by_type(BaseTester, RandomTester)
        self.env = Environment("env", self)


class MaxTest(uvm_test):
    """Run with max operands"""
    def build_phase(self):
        uvm_factory().set_type_override_by_type(BaseTester, MaxTester)
        self.env = Environment("env", self)


@cocotb.test()
async def random_test(_):
    """Random operands"""
    await uvm_root().run_test(RandomTest)


@cocotb.test()
async def max_test(_):
    """Maximum operands"""
    await uvm_root().run_test(MaxTest)
