import pyuvm
from pyuvm import *


# # uvm_component
# ## Running the phases

# Figure 1: A uvm_test demonstrating the phase methods
@pyuvm.test()
class PhaseTest(uvm_test):  # uvm_test extends uvm_component
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


# ## Building the testbench hierarchy
# ### TestTop (uvm_test_top)

# Figure 4: pyuvm instantiates TestTop as uvm_test_top
# The test is always named uvm_test_top

@pyuvm.test()
class TestTop(uvm_test):
    def build_phase(self):
        self.logger.info(f"{self.get_name()} build_phase")
        self.mc = MiddleComp("mc", self)

    def final_phase(self):
        self.logger.info("final phase")


# ### MiddleComp (uvm_test_top.mc)
# Figure 5: The middle component is instantiated by
# uvm_test_top as "mc" and instantiates "bc".
class MiddleComp(uvm_component):
    def build_phase(self):
        self.bc = BottomComp(name="bc", parent=self)

    def end_of_elaboration_phase(self):
        self.logger.info(f"{self.get_name()} end of elaboration phase")


# ### BottomComp (uvm_test_top.mc.bc)
# Figure 6: The bottom component is instantiated by
# the middle component and is at "uvm_test_top.mc.bc"
class BottomComp(uvm_component):
    async def run_phase(self):
        self.raise_objection()
        self.logger.info(f"{self.get_name()} run phase")
        self.drop_objection()
