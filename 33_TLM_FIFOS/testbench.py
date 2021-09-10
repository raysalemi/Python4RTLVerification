import cocotb
from cocotb.triggers import Timer
from pyuvm import *
import random


# Blocking Ports


class BlockingProducer(uvm_component):
    def build_phase(self):
        self.pp = uvm_put_port("pp", self)

    async def run_phase(self):
        self.raise_objection()
        for nn in range(3):
            await self.pp.put(nn)
            print(f"Put {nn}", end=" ")
        self.drop_objection()


class BlockingConsumer(uvm_component):
    def build_phase(self):
        self.gp = uvm_get_port("gp", self)

    async def run_phase(self):
        while True:
            nn = await self.gp.get()
            print(f"Got {nn}", end=" ")


class BlockingFIFOTest(uvm_test):
    def build_phase(self):
        self.prod = BlockingProducer("prod", self)
        self.cons = BlockingConsumer("cons", self)
        self.fifo = uvm_tlm_fifo("fifo", self)

    def connect_phase(self):
        self.prod.pp.connect(self.fifo.put_export)
        self.cons.gp.connect(self.fifo.get_export)


@cocotb.test()
async def blocking_fifo(dut):
    """Blocking FIFO example"""
    await uvm_root().run_test("BlockingFIFOTest")
    assert True


# Nonblocking FIFO


class NonBlockingProducer(uvm_component):
    def build_phase(self):
        self.pp = uvm_put_port("pp", self)

    async def run_phase(self):
        self.raise_objection()
        for nn in range(3):
            success = False
            while not success:
                success = self.pp.try_put(nn)
                if success:
                    print(f"Put {nn}")
                else:
                    sleep_time = random.randint(1, 10)
                    print(f"Failed to put {nn}. Sleep {sleep_time}")
                    await Timer(sleep_time)
        await Timer(1)
        self.drop_objection()


class NonBlockingConsumer(uvm_component):
    def build_phase(self):
        self.gp = uvm_get_port("gp", self)

    async def run_phase(self):
        while True:
            success = False
            while not success:
                success, nn = self.gp.try_get()
                if success:
                    print(f"Got {nn}")
                else:
                    sleep_time = random.randint(1, 10)
                    print(f"Failed to get. Sleep {sleep_time}")
                    await Timer(sleep_time)


class NonBlockingFIFOTest(uvm_test):
    def build_phase(self):
        self.prod = NonBlockingProducer("prod", self)
        self.cons = NonBlockingConsumer("cons", self)
        self.fifo = uvm_tlm_fifo("fifo", self)

    def connect_phase(self):
        self.prod.pp.connect(self.fifo.put_export)
        self.cons.gp.connect(self.fifo.get_export)


@cocotb.test()
async def non_blocking_fifo(dut):
    """Blocking FIFO example"""

    await uvm_root().run_test("NonBlockingFIFOTest")
    assert True
