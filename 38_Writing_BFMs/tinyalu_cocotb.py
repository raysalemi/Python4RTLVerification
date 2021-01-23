from cocotb.clock import Clock
from cocotb.triggers import FallingEdge, RisingEdge
from cocotb.result import *
import cocotb
from pyuvm import *


class AluBfm:
    def __init__(self, dut, label):
        self.dut = dut
        ConfigDB().set(None, "*", label, self)
        self.driver_queue = UVMQueue(maxsize=1)
        self.cmd_mon_queue = UVMQueue(maxsize=0)
        self.result_mon_queue = UVMQueue(maxsize=0)
        self.done = cocotb.triggers.Event(name="Done")

    async def send_op(self, aa, bb, op):
        self.driver_queue.put((aa, bb, op))

    def get_cmd(self):
        try:
            cmd = self.cmd_mon_queue.get_nowait()
        except queue.Empty:
            cmd = None
        return cmd

    def get_result(self):
        try:
            result = self.result_mon_queue.get_nowait()
        except queue.Empty:
            result = None
        return result

    async def reset(self):
        await FallingEdge(self.dut.clk)
        self.dut.reset_n = 0
        self.dut.A = 0
        self.dut.B = 0
        self.dut.op = 0
        await FallingEdge(self.dut.clk)
        self.dut.reset_n = 1
        await FallingEdge(self.dut.clk)

    async def start(self):
        cocotb.fork(self.driver_bfm())
        cocotb.fork(self.cmd_mon_bfm())
        cocotb.fork(self.result_mon_bfm())
        pass

    async def driver_bfm(self):
        self.dut.start = self.dut.A = self.dut.B = 0
        self.dut.op = 0
        while True:
            await FallingEdge(self.dut.clk)
            if self.dut.start == 0 and self.dut.done == 0:
                try:
                    (aa, bb, op) = self.driver_queue.get_nowait()
                    time.sleep(0.1)
                    self.dut.A = aa
                    self.dut.B = bb
                    self.dut.op = op
                    self.dut.start = 1
                except queue.Empty:
                    pass
            elif self.dut.start == 1:
                if self.dut.done.value == 1:
                    self.dut.start = 0

    async def cmd_mon_bfm(self):
        prev_start = 0
        while True:
            await FallingEdge(self.dut.clk)
            try:
                start = int(self.dut.start.value)
            except ValueError:
                start = 0
            if start == 1 and prev_start == 0:
                self.cmd_mon_queue.put_nowait((int(self.dut.A), int(self.dut.B), int(self.dut.op)))
            prev_start = start

    async def result_mon_bfm(self):
        prev_done = 0
        while True:
            await FallingEdge(self.dut.clk)
            try:
                done = int(self.dut.done)
            except ValueError:
                done = 0

            if done == 1 and prev_done == 0:
                self.result_mon_queue.put_nowait(int(self.dut.result))
            prev_done = done


def raise_objection():
    uvm_root().raise_objection()


def drop_objection():
    root = uvm_root()
    root.drop_objection()

async def sleep():
    time.sleep(3)
# noinspection PyArgumentList
@cocotb.test()
async def test_alu(dut):
    raise_objection()
    clock = Clock(dut.clk, 2, units="us")
    cocotb.fork(clock.start())
    bfm = AluBfm(dut, "BFM")
    await bfm.reset()
    cocotb.fork(bfm.start())
    await FallingEdge(dut.clk)
    await bfm.send_op(0xAA, 0x55, 1)
    await cocotb.triggers.ClockCycles(dut.clk, 5)
    cmd = bfm.get_cmd()
    result = bfm.get_result()
    print("cmd:",cmd)
    print("result:", result)
    if result != 0xFF:
        drop_objection()
        raise TestFailure (f"ERROR: Bad answer {result:x} should be 0xFF")
    else:
        drop_objection()
        raise TestSuccess
