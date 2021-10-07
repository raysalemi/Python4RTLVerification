import cocotb
from cocotb.triggers import FallingEdge
from cocotb.queue import QueueEmpty, Queue
import enum
import random
import logging

logging.basicConfig(level=logging.NOTSET)
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)


@enum.unique
class Ops(enum.IntEnum):
    """Legal ops for the TinyALU"""
    ADD = 1
    AND = 2
    XOR = 3
    MUL = 4


def alu_prediction(A, B, op, error=False):
    """Python model of the TinyALU"""
    assert isinstance(op, Ops), "The tinyalu op must be of type ops"
    if op == Ops.ADD:
        result = A + B
    elif op == Ops.AND:
        result = A & B
    elif op == Ops.XOR:
        result = A ^ B
    elif op == Ops.MUL:
        result = A * B
    if error and (random.randint(0, 3) == 0):
        result = result + 1
    return result


def get_int(signal):
    try:
        sig = int(signal)
    except ValueError:
        sig = 0
    return sig


class TinyAluBfm:
    def __init__(self, dut):
        self.dut = dut
        self.driver_queue = Queue(maxsize=1)
        self.cmd_mon_queue = Queue(maxsize=0)
        self.result_mon_queue = Queue(maxsize=0)

    async def send_op(self, aa, bb, op):
        command_tuple = (aa, bb, op)
        await self.driver_queue.put(command_tuple)

    async def get_cmd(self):
        cmd = await self.cmd_mon_queue.get()
        return cmd

    async def get_result(self):
        result = await self.result_mon_queue.get()
        return result

    async def reset(self):
        await FallingEdge(self.dut.clk)
        self.dut.reset_n <= 0
        self.dut.A <= 0
        self.dut.B <= 0
        self.dut.op <= 0
        await FallingEdge(self.dut.clk)
        self.dut.reset_n <= 1
        await FallingEdge(self.dut.clk)

    async def driver_bfm(self):
        self.dut.start <= 0
        self.dut.A <= 0
        self.dut.B <= 0
        self.dut.op <= 0
        while True:
            await FallingEdge(self.dut.clk)
            start = get_int(self.dut.start.value)
            done = get_int(self.dut.done.value)
            if start == 0 and done == 0:
                try:
                    (aa, bb, op) = self.driver_queue.get_nowait()
                    self.dut.A <= aa
                    self.dut.B <= bb
                    self.dut.op <= op
                    self.dut.start <= 1
                except QueueEmpty:
                    pass
            elif start == 1:
                if done == 1:
                    self.dut.start = 0

    async def cmd_mon_bfm(self):
        prev_start = 0
        while True:
            await FallingEdge(self.dut.clk)
            start = get_int(self.dut.start.value)
            if start == 1 and prev_start == 0:
                cmd_tuple = (int(self.dut.A),
                             int(self.dut.B),
                             int(self.dut.op))
                self.cmd_mon_queue.put_nowait(cmd_tuple)
            prev_start = start

    async def result_mon_bfm(self):
        prev_done = 0
        while True:
            await FallingEdge(self.dut.clk)
            done = get_int(self.dut.done.value)
            if prev_done == 0 and done == 1:
                result = get_int(self.dut.result.value)
                self.result_mon_queue.put_nowait(result)
            prev_done = done

    async def start_bfms(self):
        cocotb.fork(self.driver_bfm())
        cocotb.fork(self.cmd_mon_bfm())
        cocotb.fork(self.result_mon_bfm())
