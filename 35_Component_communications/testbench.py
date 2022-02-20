import pyuvm
from cocotb.triggers import Timer
from pyuvm import *


# # Component communication
# ## Ports
# Figure 1: A producer that blocks on a full FIFO
class BlockingProducer(uvm_component):
    def build_phase(self):
        self.bpp = uvm_blocking_put_port("bpp", self)

    async def run_phase(self):
        self.raise_objection()
        for nn in range(3):
            await self.bpp.put(nn)
            self.logger.info(f"Put {nn}")
        self.drop_objection()


# Figure 2: A consumer that blocks on an empty FIFO
class BlockingConsumer(uvm_component):
    def build_phase(self):
        self.bgp = uvm_blocking_get_port("bgp", self)

    async def run_phase(self):
        while True:
            nn = await self.bgp.get()
            self.logger.info(f"Got {nn}")


# ## uvm_tlm_fifo
# Figure 4: The connect_phase() in action

@pyuvm.test()
class BlockingTest(uvm_test):
    def build_phase(self):
        self.producer = BlockingProducer("producer", self)
        self.consumer = BlockingConsumer("consumer", self)
        self.fifo = uvm_tlm_fifo("fifo", self)

    def connect_phase(self):
        self.producer.bpp.connect(self.fifo.put_export)
        self.consumer.bgp.connect(self.fifo.get_export)


# ## Non-blocking communication in pyuvm
# Figure 6: A producer that does not block on an full FIFO
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
                    await Timer(1, units="ns")
        await Timer(3, units="ns")
        self.drop_objection()


# Figure 7: A consumer that does not block on an empty FIFO
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
                    await Timer(3, units="ns")


# Figure 8: Connecting the nonblocking components

@pyuvm.test()
class NonBlockingTest(uvm_test):
    def build_phase(self):
        self.producer = NonBlockingProducer("producer", self)
        self.consumer = NonBlockingConsumer("consumer", self)
        self.fifo = uvm_tlm_fifo("fifo", self)

    def connect_phase(self):
        self.producer.nbpp.connect(self.fifo.put_export)
        self.consumer.nbgp.connect(self.fifo.get_export)


# ## Debugging uvm_tlm_fifo
# Figure 11: Enabling log messages from uvm_tlm_fifo
@pyuvm.test()
class LoggedBlockingtest(BlockingTest):
    def end_of_elaboration_phase(self):
        self.fifo.set_logging_level_hier(FIFO_DEBUG)
