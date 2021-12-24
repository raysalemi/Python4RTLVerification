import cocotb
from pyuvm import *


# # uvm_component
# ## Running the phases
class PhaseTest(uvm_test):
    def build_phase(self):
        print("1 build_phase")

    def connect_phase(self):
        print("2 connect_phase")

    def end_of_elaboration_phase(self):
        print("3 end_of_elaboration_phase")

    def start_of_simulation_phase(self):
        print("4 start_of_simulation_phase")

    async def run_phase(self):
        self.raise_objection()
        print("5 run_phase")
        self.drop_objection()

    def extract_phase(self):
        print("6 extract_phase")

    def check_phase(self):
        print("7 check_phase")

    def report_phase(self):
        print("8 report_phase")

    def final_phase(self):
        print("9 final_phase")


@cocotb.test()
async def phase_test(dut):
    """print out the phases"""
    await uvm_root().run_test(PhaseTest)
    assert True


# ## Building the testbench hierarchy
# ### TestTop (uvm_test_top)
class TestTop(uvm_test):
    def build_phase(self):
        self.mc = MiddleComp("mc", self)

    def final_phase(self):
        self.logger.info(f"{self.get_name()} final phase")


# ### MiddleComp (uvm_test_top.mc)
class MiddleComp(uvm_component):
    def build_phase(self):
        self.bc = BottomComp(name="bc", parent=self)

    def end_of_elaboration_phase(self):
        self.logger.info(f"{self.get_name()} end of elaboration phase")


# ### BottomComp (uvm_test_top.mc.bc)
class BottomComp(uvm_component):
    async def run_phase(self):
        self.raise_objection()
        self.logger.info(f"{self.get_name()} run phase")
        self.drop_objection()


@cocotb.test()
async def hierarchy_test(dut):
    """Create hierarchy"""
    await uvm_root().run_test(TestTop)
