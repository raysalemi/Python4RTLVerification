import cocotb
from pyuvm import *


class SeqItem(uvm_sequence_item):
    def __init__(self, name):
        super().__init__(name)
        self.numb = self.result = None

    def __str__(self):
        return f"numb: {self.numb}   result: {self.result}"


class SeqDriver(uvm_driver):
    async def run_phase(self):
        while True:
            op_item = await self.seq_item_port.get_next_item()
            op_item.result = op_item.numb + 1
            self.seq_item_port.item_done()


class Seq(uvm_sequence):
    async def body(self):
        for nn in range(5):
            op = SeqItem("op")
            await self.start_item(op)
            op.numb = nn
            await self.finish_item(op)
            print(op)


class SeqTest(uvm_test):
    def build_phase(self):
        self.seqr = uvm_sequencer("seqr", self)
        self.drvr = SeqDriver("drvr", self)

    def connect_phase(self):
        self.drvr.seq_item_port.connect(self.seqr.seq_item_export)

    async def run_phase(self):
        self.raise_objection()
        self.seq = Seq.create("seq")
        await self.seq.start(self.seqr)
        self.drop_objection()


@cocotb.test()
async def sequences(dut):
    """Demonstrate basic sequence usage"""
    await uvm_root().run_test("SeqTest")
    assert True


class HelloSeq(uvm_sequence):
    async def body(self):
        print("Hello World")


class HelloTest(uvm_test):
    async def run_phase(self):
        self.raise_objection()
        self.hello = HelloSeq("hello")
        await self.hello.start()
        self.drop_objection()


@cocotb.test()
async def virtual_sequence(dut):
    """Demonstrate virtual sequences"""
    await uvm_root().run_test("HelloTest")
    assert True
