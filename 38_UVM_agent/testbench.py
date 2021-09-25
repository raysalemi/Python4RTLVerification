import cocotb
from cocotb.triggers import Timer
from pyuvm import *
import random
# All testbenches use tinyalu_utils, so store it in a central
# place and add its path to the sys path so we can import it
import sys
from pathlib import Path
sys.path.append(str(Path("..").resolve()))
from tinyalu_utils import TinyAluBfm, Ops, alu_prediction  # noqa: E402


class Driver(uvm_component):
    def build_phase(self):
        self.bfm = self.cdb_get("BFM")

    async def run_phase(self):
        self.raise_objection()
        for _ in range(5):
            aa = random.randrange(256)
            bb = random.randrange(256)
            op = random.choice(list(Ops))
            await self.bfm.send_op(aa, bb, op)
        Timer(200)
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
                if predicted_result == actual_result:
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


class AluAgent(uvm_agent):
    def build_phase(self):
        super().build_phase()

        if self.active():
            self.driver = Driver.create("driver", self)

        try:
            self.is_monitor = ConfigDB().get(self, "", "is_monitor")
        except UVMConfigItemNotFound:
            self.is_monitor = True

        if self.is_monitor:
            self.cmd_mon = Monitor("cmd_mon", self, "get_cmd")
            self.result_mon = Monitor("result_mon", self, "get_result")

    def connect_phase(self):
        if self.is_monitor:
            self.cmd_ap = self.cmd_mon.ap
            self.result_ap = self.result_mon.ap


class AluEnv(uvm_env):

    def build_phase(self):

        # active agent drives stimulus, passive agent monitors it

        self.cdb_set("is_active", uvm_active_passive_enum.UVM_ACTIVE,
                     inst_path="active*")
        self.cdb_set("is_monitor", False, inst_path="active*")

        self.cdb_set("is_active", uvm_active_passive_enum.UVM_PASSIVE,
                     inst_path="passive*")

        self.active_agent = AluAgent("active_agent", self)
        self.passive_agent = AluAgent("passive_agent", self)
        self.scoreboard = Scoreboard.create("scoreboard", self)
        self.coverage = Coverage.create("coverage", self)

    def connect_phase(self):
        # For scoreboard
        self.passive_agent.cmd_ap.connect(self.scoreboard.cmd_export)
        self.passive_agent.result_ap.connect(self.scoreboard.result_export)

        # For coverage
        self.passive_agent.cmd_ap.connect(self.coverage)


class AluTest(uvm_test):
    def build_phase(self):
        self.env = AluEnv("env", self)


@cocotb.test()
async def max_env(dut):
    """
    Demonstrates using an environment to run a different test
    """
    bfm = TinyAluBfm(dut)
    ConfigDB().set(None, "*", "BFM", bfm)
    await bfm.start_bfms()
    await uvm_root().run_test("AluTest")
    assert True
