import cocotb
from cocotb.triggers import Timer
from pyuvm import *


class PhaseTest(uvm_test):
    def build_phase(self):
        self.logger.info("build_phase: Adds components")

    def connect_phase(self):
        self.logger.info("connect_phase: Connects components")

    def end_of_elaboration_phase(self):
        self.logger.info("end_of_elaboration_phase: Testbench is built")

    def start_of_simulation_phase(self):
        self.logger.info("start_of_simulation_phase: Ready to sim")

    async def run_phase(self):
        self.raise_objection()
        await Timer(2, units="ns")
        self.logger.info("run_phase: Simulate and consume time")
        self.drop_objection()

    def extract_phase(self):
        self.logger.info("extract_phase: Simulation is over. Gather data")

    def check_phase(self):
        self.logger.info("check_phase: Check the results")

    def report_phase(self):
        self.logger.info("report_phase: Report the results")

    def final_phase(self):
        self.logger.info("final_phase: Final clean up")


@cocotb.test()
async def phase_test(dut):
    """print out the phases"""
    await uvm_root().run_test(PhaseTest)
    assert True


class BottomComp(uvm_component):
    async def run_phase(self):
        self.raise_objection()
        await Timer(1, units="ns")
        self.logger.info(f"{self.get_name()} run phase")
        self.drop_objection()


class MiddleComp(uvm_component):
    def build_phase(self):
        self.bc = BottomComp(name="bc", parent=self)

    def end_of_elaboration_phase(self):
        self.logger.info(f"{self.get_name()} end of elaboration phase")


class TopTest(uvm_test):
    def build_phase(self):
        self.mc = MiddleComp("mc", self)

    def final_phase(self):
        self.logger.info(f"{self.get_name()} final phase")


@cocotb.test()
async def hierarchy_test(dut):
    """Create hierarchy"""
    await uvm_root().run_test(TopTest)
