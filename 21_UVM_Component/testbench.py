import cocotb
from pyuvm import *


class PhaseTest(uvm_test):
    def build_phase(self):
        self.logger.info("build_phase adds components")

    def connect_phase(self):
        self.logger.info("connect_phase adds components")

    def end_of_elaboration_phase(self):
        self.logger.info("end_of_elsaboration_phase means everything is built and connected")

    def start_of_simulation_phase(self):
        self.logger.info("start_of_simulation_phase is the last chance before simulation starts")

    async def run_phase(self):
        self.raise_objection()
        self.logger.info("run_phase launches the thread that does the work ")
        self.drop_objection()

    def extract_phase(self):
        self.logger.info("extract_phase runs after all threads end. Gather data for checking")

    def check_phase(self):
        self.logger.info("check_phase is for checking that you had no errors")

    def report_phase(self):
        self.logger.info("report_phase is where you report results")

    def final_phase(self):
        self.logger.info("final_phase is for clean up tasks for ending")


@cocotb.test()
async def phase_test(dut):
    """print out the phases"""
    await uvm_root().run_test("PhaseTest")
    assert True

class BottomComp(uvm_component):
    async def run_phase(self):
        self.raise_objection()
        self.logger.info(f"{self.get_name()} is running")   
        self.drop_objection()

class MiddleComp(uvm_component):
    def build_phase(self):
        self.bc = BottomComp(name="bc", parent=self)
    
    def end_of_elaboration_phase(self):
        self.logger.info(f"{self.get_name()} is here")
        
class TopTest(uvm_test):
    def build_phase(self):
        self.mc = MiddleComp("mc", self)
    
    def end_of_elaboration_phase(self):
        self.logger.info(f"{self.get_name()} is here")


@cocotb.test()
async def phase_test(dut):
    """Create hierarchy"""
    await uvm_root().run_test("TopTest")
    assert True
