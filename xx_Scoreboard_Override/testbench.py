import cocotb
from cocotb.triggers import Timer
from pyuvm import *
from tinyalu_utils import TinyAluBfm, alu_prediction, Ops
import random


class Driver(uvm_component):
    def build_phase(self):
        self.bfm = self.cdb_get("BFM")

    async def run_phase(self):
        self.raise_objection()
        for op in list(Ops):
            aa = random.randrange(256)
            bb = random.randrange(256)
            await self.bfm.send_op(aa, bb, int(op))
        await Timer(200)
        self.drop_objection()


class Coverage(uvm_subscriber):

    def end_of_elaboration_phase(self):
        self.cvg = set()

    def write(self, cmd):
        (_, _, op) = cmd
        self.cvg.add(op)

    def check_phase(self):
        if len(set(Ops) - self.cvg) > 0:
            self.logger.error(f"Functional coverage "
                              f"error. Missed: {set(Ops)-self.cvg}")


class Scoreboard(uvm_component):

    def same(self, predicted, actual):
        return predicted == actual

    def build_phase(self):
        self.cmd_fifo = uvm_tlm_analysis_fifo("cmd_fifo", self)
        self.result_fifo = uvm_tlm_analysis_fifo("result_fifo", self)
        self.cmd_get_port = uvm_get_port("cmd_get_port", self)
        self.result_get_port = uvm_get_port("result_get_port", self)
        self.cmd_export = self.cmd_fifo.analysis_export
        self.result_export = self.result_fifo.analysis_export

    def connect_phase(self):
        self.cmd_get_port.connect(self.cmd_fifo.get_export)
        self.result_get_port.connect(self.result_fifo.get_export)

    def check_phase(self):
        while self.result_get_port.can_get():
            _, actual_result = self.result_get_port.try_get()
            cmd_success, (A, B, op_numb) = self.cmd_get_port.try_get()
            if not cmd_success:
                self.logger.critical(f"result {actual_result} had no command")
            else:
                op = Ops(op_numb)
                predicted_result = alu_prediction(A, B, op)
                if self.same(predicted_result, actual_result):
                    self.logger.info(f"PASSED: 0x{A:02x} {op.name} 0x{B:02x} ="
                                     f" 0x{actual_result:04x}")
                else:
                    self.logger.error(f"FAILED: 0x{A:02x} {op.name} 0x{B:02x} "
                                      f"= 0x{actual_result:04x} expected 0x{predicted_result:04x}")


class Monitor(uvm_component):
    def __init__(self, name, parent, method_name):
        super().__init__(name, parent)
        self.method_name = method_name

    def build_phase(self):
        self.bfm = self.cdb_get("BFM")
        self.ap = uvm_analysis_port("ap", self)

    async def run_phase(self):
        while True:
            get_method = getattr(self.bfm, self.method_name)
            datum = await get_method()
            self.ap.write(datum)


class AluEnv(uvm_env):

    def build_phase(self):
        self.cmd_mon = Monitor("cmd_mon", self, "get_cmd")
        self.result_mon = Monitor("result_mon", self, "get_result")
        self.scoreboard = Scoreboard.create("scoreboard", self)
        self.coverage = Coverage("coverage", self)
        self.driver = Driver("driver", self)
        ConfigDB().set(None, "*", "CVG", self.coverage)

    def connect_phase(self):
        self.cmd_mon.ap.connect(self.scoreboard.cmd_export)
        self.cmd_mon.ap.connect(self.coverage)
        self.result_mon.ap.connect(self.scoreboard.result_export)


class AluTest(uvm_test):
    def build_phase(self):
        self.env = AluEnv("env", self)


class FaultyScoreboard(Scoreboard):
    def same(self, predicted, actual):
        if random.randint(0, 1) == 1:
            predicted += 1  # Python for ++
        return super().same(predicted, actual)


class FaultyTest(AluTest):
    def build_phase(self):
        uvm_factory().set_type_override_by_type(Scoreboard, FaultyScoreboard)
        super().build_phase()


@cocotb.test()
async def good_scoreboard(dut):
    """
    Demonstrates the correct scoreboard
    """
    bfm = TinyAluBfm(dut)
    await bfm.startup_bfms()
    ConfigDB().set(None, "*", "BFM", bfm)
    await uvm_root().run_test("AluTest")
    assert True


@cocotb.test()
async def faulty_scoreboard(dut):
    """
    Demonstrates overriding the scoreboard with a bad one
    """
    bfm = TinyAluBfm(dut)
    await bfm.startup_bfms()
    ConfigDB().set(None, "*", "BFM", bfm)
    await uvm_root().run_test("FaultyTest")
    assert True
