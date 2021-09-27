import cocotb
from pyuvm import *

# Basic Logging


class LogComp(uvm_component):
    async def run_phase(self):
        self.raise_objection()
        self.logger.debug("This is debug")
        self.logger.info("This is info")
        self.logger.warning("This is warning")
        self.logger.error("This is error")
        self.logger.critical("This is critical")
        self.logger.log(FIFO_DEBUG, "This is a FIFO message")
        self.drop_objection()


class LogTest(uvm_test):
    def build_phase(self):
        self.comp = LogComp("comp", self)


class DebugTest(LogTest):
    def end_of_elaboration_phase(self):
        self.set_logging_level_hier(DEBUG)


class FifoDebugTest(LogTest):
    def end_of_elaboration_phase(self):
        self.set_logging_level_hier(DEBUG)



@cocotb.test()
async def logging_example(dut):
    """Demonstrate basic logging"""
    await uvm_root().run_test("LogTest")
    assert True


# Set logging levels


class Producer(uvm_component):
    def build_phase(self):
        self.pp = uvm_put_port("pp", self)

    async def run_phase(self):
        self.raise_objection()
        for nn in range(5):
            await self.pp.put(nn)
            print(f"Put {nn}", end=" ")
        self.drop_objection()


class Consumer(uvm_component):
    def build_phase(self):
        self.gp = uvm_get_port("gp", self)

    async def run_phase(self):
        while True:
            nn = await self.gp.get()
            print(f"Got {nn}", end=" ")


class FIFOTest(uvm_test):
    def build_phase(self):
        self.prod = Producer("prod", self)
        self.cons = Consumer("cons", self)
        self.fifo = uvm_tlm_fifo("fifo", self)

    def end_of_elaboration_phase(self):
        self.set_logging_level_hier(FIFO_DEBUG)

    def connect_phase(self):
        self.prod.pp.connect(self.fifo.put_export)
        self.cons.gp.connect(self.fifo.get_export)


@cocotb.test()
async def logging_levels(dut):
    """Demonstrate logging levels"""
    await uvm_root().run_test("FIFOTest")
    assert True


class FileFIFOTest(uvm_test):
    def build_phase(self):
        self.prod = Producer("prod", self)
        self.cons = Consumer("cons", self)
        self.fifo = uvm_tlm_fifo("fifo", self)

    def end_of_elaboration_phase(self):
        file_handler = logging.FileHandler("put.txt")
        self.add_logging_handler_hier(file_handler)
        self.set_logging_level_hier(FIFO_DEBUG)

    def connect_phase(self):
        self.prod.pp.connect(self.fifo.put_export)
        self.cons.gp.connect(self.fifo.get_export)


@cocotb.test()
async def logging_to_a_file(dut):
    """Demonstrate logging to a file"""
    await uvm_root().run_test("FileFIFOTest")
    assert True
