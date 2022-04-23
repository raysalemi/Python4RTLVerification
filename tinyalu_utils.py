import cocotb
from cocotb.triggers import FallingEdge
from cocotb.queue import QueueEmpty, Queue
import enum
import logging
import pyuvm


# #### The OPS enumeration

# Figure 4: The operation enumeration
@enum.unique
class Ops(enum.IntEnum):
    """Legal ops for the TinyALU"""
    ADD = 1
    AND = 2
    XOR = 3
    MUL = 4


# #### The alu_prediction function

# Figure 5: The prediction function for the scoreboard
def alu_prediction(A, B, op):
    """Python model of the TinyALU"""
    assert isinstance(op, Ops), "The tinyalu op must be of type Ops"
    if op == Ops.ADD:
        result = A + B
    elif op == Ops.AND:
        result = A & B
    elif op == Ops.XOR:
        result = A ^ B
    elif op == Ops.MUL:
        result = A * B
    return result


# #### The logger

# Figure 6: Setting up logging using the logger variable
logging.basicConfig(level=logging.NOTSET)
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)


# ### Reading a signal value
# Figure 6: get_int() converts a bus to an integer
# turning a value of x or z to 0
def get_int(signal):
    try:
        int_val = int(signal.value)
    except ValueError:
        int_val = 0
    return int_val


# ## The TinyAluBfm singleton
# ### Initializing the TinyAluBfm object


# Figure 3: Initializing the TinyAluBfm singleton
class TinyAluBfm(metaclass=pyuvm.Singleton):
    def __init__(self):
        self.dut = cocotb.top
        self.cmd_driver_queue = Queue(maxsize=1)
        self.cmd_mon_queue = Queue(maxsize=0)
        self.result_mon_queue = Queue(maxsize=0)

# ### The reset coroutine

# Figure 4: Centralizing the reset function
    async def reset(self):
        await FallingEdge(self.dut.clk)
        self.dut.reset_n.value = 0
        self.dut.A.value = 0
        self.dut.B.value = 0
        self.dut.op.value = 0
        await FallingEdge(self.dut.clk)
        self.dut.reset_n.value = 1
        await FallingEdge(self.dut.clk)

# ## The communication coroutines
# #### result_mon()

# Figure 6: Monitoring the result bus
    async def result_mon(self):
        prev_done = 0
        while True:
            await FallingEdge(self.dut.clk)
            done = get_int(self.dut.done)
            if prev_done == 0 and done == 1:
                result = get_int(self.dut.result)
                self.result_mon_queue.put_nowait(result)
            prev_done = done

# #### cmd_mon()
# Figure 7: Monitoring the command signals
    async def cmd_mon(self):
        prev_start = 0
        while True:
            await FallingEdge(self.dut.clk)
            start = get_int(self.dut.start)
            if start == 1 and prev_start == 0:
                cmd_tuple = (get_int(self.dut.A),
                             get_int(self.dut.B),
                             get_int(self.dut.op))
                self.cmd_mon_queue.put_nowait(cmd_tuple)
            prev_start = start

# #### driver()
# Figure 8: Driving commands on the falling edge of clk
    async def cmd_driver(self):
        self.dut.start.value = 0
        self.dut.A.value = 0
        self.dut.B.value = 0
        self.dut.op.value = 0
        while True:
            await FallingEdge(self.dut.clk)
            st = get_int(self.dut.start)
            dn = get_int(self.dut.done)
# Figure 9: Driving commands to the TinyALU when
# start and done are 0
            if st == 0 and dn == 0:
                try:
                    (aa, bb, op) = self.cmd_driver_queue.get_nowait()
                    self.dut.A.value = aa
                    self.dut.B.value = bb
                    self.dut.op.value = op
                    self.dut.start.value = 1
                except QueueEmpty:
                    continue
# Figure 10: If start is 1 check done
            elif st == 1:
                if dn == 1:
                    self.dut.start.value = 0

# ### Launching the coroutines using start_soon
# Figure 11: Start the BFM coroutines
    def start_tasks(self):
        cocotb.start_soon(self.cmd_driver())
        cocotb.start_soon(self.cmd_mon())
        cocotb.start_soon(self.result_mon())

# Figure 12: The get_cmd() coroutine returns the next command
    async def get_cmd(self):
        cmd = await self.cmd_mon_queue.get()
        return cmd

# Figure 13: The get_result() coroutine returns the next result
    async def get_result(self):
        result = await self.result_mon_queue.get()
        return result

# Figure 14: send_op puts the command into the command Queue
    async def send_op(self, aa, bb, op):
        command_tuple = (aa, bb, op)
        await self.cmd_driver_queue.put(command_tuple)
