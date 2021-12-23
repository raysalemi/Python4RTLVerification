import cocotb
from cocotb.triggers import Timer
from pyuvm import *


class BlockingProducer(uvm_component):
    def build_phase(self):
        self.bpp = uvm_blocking_put_port("bpp", self)

    async def run_phase(self):
        self.raise_objection()
        for nn in range(3):
            await self.bpp.put(nn)
            self.logger.info(f"Put {nn}")
        self.drop_objection()


class BlockingConsumer(uvm_component):
    def build_phase(self):
        self.bgp = uvm_blocking_get_port("bgp", self)

    async def run_phase(self):
        while True:
            nn = await self.bgp.get()
            self.logger.info(f"Got {nn}")


class BlockingTest(uvm_test):
    def build_phase(self):
        self.producer = BlockingProducer("producer", self)
        self.consumer = BlockingConsumer("consumer", self)
        self.fifo = uvm_tlm_fifo("fifo", self)

    def connect_phase(self):
        self.producer.bpp.connect(self.fifo.put_export)
        self.consumer.bgp.connect(self.fifo.get_export)


@cocotb.test()
async def blocking_test(_):
    """Demonstrate blocking"""
    await uvm_root().run_test("BlockingTest")


class NonBlockingProducer(uvm_component):
    def build_phase(self):
        self.nbpp = uvm_nonblocking_put_port("nbpp", self)

    async def run_phase(self):
        self.raise_objection()
        for nn in range(3):
            self.logger.info(f"Putting: {nn}")
            success = False
            while not success:
                success = self.nbpp.try_put(nn)
                if success:
                    self.logger.info(f"Put {nn}")
                else:
                    self.logger.info("FIFO full")
                    await Timer(1, units="us")
        await Timer(3, units="us")
        self.drop_objection()


class NonBlockingConsumer(uvm_component):
    def build_phase(self):
        self.nbgp = uvm_nonblocking_get_port("nbgp", self)

    async def run_phase(self):
        while True:
            success = False
            while not success:
                success, nn = self.nbgp.try_get()
                if success:
                    self.logger.info(f"Got {nn}")
                else:
                    self.logger.info("FIFO empty")
                    await Timer(3, units="us")


class NonBlockingTest(uvm_test):
    def build_phase(self):
        self.producer = NonBlockingProducer("producer", self)
        self.consumer = NonBlockingConsumer("consumer", self)
        self.fifo = uvm_tlm_fifo("fifo", self)

    def connect_phase(self):
        self.producer.nbpp.connect(self.fifo.put_export)
        self.consumer.nbgp.connect(self.fifo.get_export)


class LoggedBlockingtest(BlockingTest):
    def end_of_elaboration_phase(self):
        self.fifo.set_logging_level_hier(FIFO_DEBUG)


@cocotb.test()
async def nonblocking_test(_):
    """Demonstrate nonblocking"""
    await uvm_root().run_test("NonBlockingTest")


@cocotb.test()
async def logged_blocking_test(_):
    """Demonstrate logging"""
    await uvm_root().run_test("LoggedBlockingtest")
