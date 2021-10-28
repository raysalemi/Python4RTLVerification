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
    await uvm_root().run_test("BlockingTest")
