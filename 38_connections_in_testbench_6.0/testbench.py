import pyuvm
from pyuvm import *
from pathlib import Path
import sys
# All testbenches use tinyalu_utils, so store it in a central
# place and add its path to the sys path so we can import it
sys.path.insert(0, str(Path("../37_components_in_testbench_6.0").resolve()))

# DRY coding.  Don't Repeat Yourself!
from component_testbench import *  # noqa: E402


# Connections in testbench 6.0
class AluEnv(uvm_env):

    # ### AluEnv.build_phase()

    # Figure 2: Instantiating the stimulus layer
    def build_phase(self):
        self.tester = BaseTester.create("tester", self)
        self.driver = Driver("driver", self)
        self.cmd_fifo = uvm_tlm_fifo("cmd_fifo", self)

        #  Figure 3: Instantiating the analysis layer
        self.scoreboard = Scoreboard("scoreboard", self)
        self.coverage = Coverage("coverage", self)

        # Figure 4: Instantiating the Monitor class by passing
        # monitoring method names
        self.cmd_mon = Monitor("cmd_monitor", self, "get_cmd")
        self.result_mon = Monitor("result_monitor", self, "get_result")

    # ### AluEnv.connect_phase()
    def connect_phase(self):

        # Figure 5: Connecting ports to the FIFO exports
        self.tester.pp.connect(self.cmd_fifo.put_export)
        self.driver.gp.connect(self.cmd_fifo.get_export)

        # Figure 6: Connecting the coverage analysis_export
        # to the cmd_mon analysis port
        self.cmd_mon.ap.connect(self.coverage)
        self.cmd_mon.ap.connect(self.scoreboard.cmd_export)
        self.result_mon.ap.connect(self.scoreboard.result_export)


# ## `RandomTest` and `MaxTest`
# Figure 7: RandomTest and MaxTest override the BaseTester

@pyuvm.test()
class RandomTest(uvm_test):
    def build_phase(self):
        uvm_factory().set_type_override_by_type(BaseTester, RandomTester)
        self.env = AluEnv("env", self)


@pyuvm.test()
class MaxTest(uvm_test):
    def build_phase(self):
        uvm_factory().set_type_override_by_type(BaseTester, MaxTester)
        self.env = AluEnv("env", self)
