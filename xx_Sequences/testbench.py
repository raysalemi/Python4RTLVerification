import cocotb
from cocotb.triggers import Join, Combine
from pyuvm import *


# Basic Sequence Operation


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


# Virtual sequences with Hello World

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


# Virtual Sequence Requirements Example (DO-254)


class Req_1101(uvm_sequence):
    async def body(self):
        print("Testing 1101")


class Req_2222(uvm_sequence):
    async def body(self):
        print("Testing 2222")


class ReqTestSeq(uvm_sequence):
    async def body(self):
        for req in ["1101", "2222"]:
            seq_name = "Req_" + req
            seq = uvm_factory().create_object_by_name(seq_name)
            await seq.start()


class ReqTest(uvm_test):
    async def run_phase(self):
        self.raise_objection()
        self.req_test = ReqTestSeq("req_test")
        await self.req_test.start()
        self.drop_objection()


@cocotb.test()
async def do254_sequence(dut):
    """Demonstrate requirements-driven testing"""
    await uvm_root().run_test("ReqTest")
    assert True


# Demonstrate passing a sequencer


class IncSeq(uvm_sequence):
    async def body(self):
        print("count up")
        for nn in range(3):
            op = SeqItem("op")
            await self.start_item(op)
            op.numb = nn
            await self.finish_item(op)
            print("Inc", op)


class DecSeq(uvm_sequence):
    async def body(self):
        print("count down")
        for nn in range(2, -1, -1):
            op = SeqItem("op")
            await self.start_item(op)
            op.numb = nn
            await self.finish_item(op)
            print("Dec", op)


class TopSeq(uvm_sequence):
    async def body(self):
        seqr = ConfigDB().get(None, "", "SEQR")
        inc = IncSeq("inc")
        await inc.start(seqr)
        dec = DecSeq("dec")
        await dec.start(seqr)


class TopSeqTest(uvm_test):
    def build_phase(self):
        self.seqr = uvm_sequencer("seqr", self)
        self.drvr = SeqDriver("drvr", self)
        ConfigDB().set(None, "*", "SEQR", self.seqr)

    def connect_phase(self):
        self.drvr.seq_item_port.connect(self.seqr.seq_item_export)

    async def run_phase(self):
        self.raise_objection()
        self.top = TopSeq("top")
        await self.top.start()
        self.drop_objection()


@cocotb.test()
async def pass_sequencer(dut):
    """Demonstrate passing a sequencer"""
    await uvm_root().run_test("TopSeqTest")
    assert True


# Forking sequences

class ForkSeq(uvm_sequence):
    async def body(self):
        seqr = ConfigDB().get(None, "", "SEQR")
        inc = IncSeq("inc")
        dec = DecSeq("dec")
        inc_co = cocotb.fork(inc.start(seqr))
        dec_co = cocotb.fork(dec.start(seqr))
        await Combine(Join(inc_co), Join(dec_co))


class ForkSeqTest(uvm_test):
    def build_phase(self):
        self.seqr = uvm_sequencer("seqr", self)
        self.drvr = SeqDriver("drvr", self)
        ConfigDB().set(None, "*", "SEQR", self.seqr)

    def connect_phase(self):
        self.drvr.seq_item_port.connect(self.seqr.seq_item_export)

    async def run_phase(self):
        self.raise_objection()
        self.fork = ForkSeq("fork")
        await self.fork.start()
        self.drop_objection()


@cocotb.test()
async def fork_sequences(dut):
    """Demonstrate running sequences in parallel"""
    await uvm_root().run_test("ForkSeqTest")
    assert True


# Returning data using item_done


class ItemDoneSeqDriver(uvm_driver):
    async def run_phase(self):
        while True:
            op_item = await self.seq_item_port.get_next_item()
            return_item = SeqItem("return_item")
            return_item.result = op_item.numb + 1
            return_item.set_context(op_item)
            self.seq_item_port.item_done(return_item)


class ItemDoneSeq(uvm_sequence):
    async def body(self):
        for nn in range(5):
            op = SeqItem("op")
            await self.start_item(op)
            op.numb = nn
            await self.finish_item(op)
            return_item = await self.get_response()
            print("Returned", return_item)


class ItemDoneTest(uvm_test):
    def build_phase(self):
        self.seqr = uvm_sequencer("seqr", self)
        self.drvr = ItemDoneSeqDriver("drvr", self)

    def connect_phase(self):
        self.drvr.seq_item_port.connect(self.seqr.seq_item_export)

    async def run_phase(self):
        self.raise_objection()
        self.seq = ItemDoneSeq.create("seq")
        await self.seq.start(self.seqr)
        self.drop_objection()


@cocotb.test()
async def item_done_ret(dut):
    """Demonstrate returning data using item_done"""
    await uvm_root().run_test("ItemDoneTest")
    assert True
