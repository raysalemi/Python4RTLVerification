import pyuvm
from pyuvm import *
import random
import statistics
# Mailbox example


# # Analysis ports
# ## The uvm_analysis_port
# Figure 1: A random number generator
class NumberGenerator(uvm_component):
    def build_phase(self):
        self.ap = uvm_analysis_port("ap", self)

    async def run_phase(self):
        self.raise_objection()
        for _ in range(9):
            nn = random.randint(1, 10)
            print(nn, end=" ")
            self.ap.write(nn)
        print("")
        self.drop_objection()


# ## Extending the uvm_analysis_export class
# Figure 2: A component to add random numbers
class Adder(uvm_analysis_export):
    def start_of_simulation_phase(self):
        self.sum = 0

    def write(self, nn):
        self.sum += nn

    def report_phase(self):
        self.logger.info(f"Sum: {self.sum}")


# Figure 3: Connecting a uvm_analysis_export to
# a uvm_analysis_port
@pyuvm.test()
class AdderTest(uvm_test):
    def build_phase(self):
        self.num_gen = NumberGenerator("num_gen", self)
        self.sum_export = Adder("sum", self)

    def connect_phase(self):
        self.num_gen.ap.connect(self.sum_export)


# ## Extend the uvm_subscriber class
# Figure 5: Using the statistics package to find the median
class Median(uvm_subscriber):

    def start_of_simulation_phase(self):
        self.numb_list = []

    def write(self, nn):
        self.numb_list.append(nn)

    def report_phase(self):
        self.logger.info(f"Median: {statistics.median(self.numb_list)}")


# Figure 6: A test that provides the sum and median
@pyuvm.test()
class MedianTest(uvm_test):
    def build_phase(self):
        self.num_gen = NumberGenerator("num_gen", self)
        self.sum_export = Adder("sum", self)
        self.median = Median("median", self)

    def connect_phase(self):
        self.num_gen.ap.connect(self.sum_export)
        self.num_gen.ap.connect(self.median.analysis_export)


# ## Instantiate a uvm_tlm_analysis_fifo
# Figure 7: A component that averages random numbers
class Average(uvm_component):
    def build_phase(self):
        self.fifo = uvm_tlm_analysis_fifo("fifo", self)
        self.nbgp = uvm_nonblocking_get_port("nbgp", self)

    def connect_phase(self):
        self.nbgp.connect(self.fifo.get_export)
        self.analysis_export = self.fifo.analysis_export

    def report_phase(self):
        success = True
        sum = 0
        count = 0
        while success:
            success, nn = self.nbgp.try_get()
            if success:
                sum += nn
                count += 1
        self.logger.info(f"Average: {sum/count:0.2f}")


# Figure 8: A test that reports sum, median, and avg
@pyuvm.test()
class AverageTest(uvm_test):
    def build_phase(self):
        self.num_gen = NumberGenerator("num_gen", self)
        self.sum_export = Adder("sum", self)
        self.median = Median("median", self)
        self.avg = Average("avg", self)

    def connect_phase(self):
        self.num_gen.ap.connect(self.sum_export)
        self.num_gen.ap.connect(self.median.analysis_export)
        self.num_gen.ap.connect(self.avg.analysis_export)
