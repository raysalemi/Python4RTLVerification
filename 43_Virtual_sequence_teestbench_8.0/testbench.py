from cocotb.triggers import Combine
from pyuvm import *
import random
import cocotb
import pyuvm
# All testbenches use tinyalu_utils, so store it in a central
# place and add its path to the sys path so we can import it
import sys
from pathlib import Path
sys.path.insert(0, str(Path("..").resolve()))
from tinyalu_utils import TinyAluBfm, Ops, alu_prediction  # noqa: E402


# # Virtual sequence testbench: 8.0
# ## Launching sequences from a virtual sequence
# Figure 1: Calling a virtual sequence
@pyuvm.test()
class AluTest(uvm_test):
    def build_phase(self):
        self.env = AluEnv("env", self)

    def end_of_elaboration_phase(self):
        self.test_all = TestAllSeq.create("test_all")

    async def run_phase(self):
        self.raise_objection()
        await self.test_all.start()
        self.drop_objection()


# Figure 2: A virtual sequence starts other sequences
class TestAllSeq(uvm_sequence):

    async def body(self):
        seqr = ConfigDB().get(None, "", "SEQR")
        rand_seq = RandomSeq("random")
        max_seq = MaxSeq("max")
        await rand_seq.start(seqr)
        await max_seq.start(seqr)


# Figure 4: Running RandomSeq and MaxSeq in parallel
class TestAllParallelSeq(uvm_sequence):

    async def body(self):
        seqr = ConfigDB().get(None, "", "SEQR")
        random_seq = RandomSeq("random")
        max_seq = MaxSeq("max")
        random_task = cocotb.start_soon(random_seq.start(seqr))
        max_task = cocotb.start_soon(max_seq.start(seqr))
        await Combine(random_task, max_task)


# ## Creating a programming interface
# ### OpSeq
# Figure 6: A sequence that can run any operation
class OpSeq(uvm_sequence):
    def __init__(self, name, aa, bb, op):
        super().__init__(name)
        self.aa = aa
        self.bb = bb
        self.op = Ops(op)

    async def body(self):
        seq_item = AluSeqItem("seq_item", self.aa, self.bb,
                              self.op)
        await self.start_item(seq_item)
        await self.finish_item(seq_item)
        self.result = seq_item.result


# ### TinyALU programming interface
# Figure 7: The programming interface coroutines
async def do_add(seqr, aa, bb):
    seq = OpSeq("seq", aa, bb, Ops.ADD)
    await seq.start(seqr)
    return seq.result


async def do_and(seqr, aa, bb):
    seq = OpSeq("seq", aa, bb, Ops.AND)
    await seq.start(seqr)
    return seq.result


async def do_xor(seqr, aa, bb):
    seq = OpSeq("seq", aa, bb, Ops.XOR)
    await seq.start(seqr)
    return seq.result


async def do_mul(seqr, aa, bb):
    seq = OpSeq("seq", aa, bb, Ops.MUL)
    await seq.start(seqr)
    return seq.result


# Figure 8: The Fibonacci program written using
# the programming interface
class FibonacciSeq(uvm_sequence):
    def __init__(self, name):
        super().__init__(name)
        self.seqr = ConfigDB().get(None, "", "SEQR")

    async def body(self):
        prev_num = 0
        cur_num = 1
        fib_list = [prev_num, cur_num]
        for _ in range(7):
            sum = await do_add(self.seqr, prev_num, cur_num)
            fib_list.append(sum)
            prev_num = cur_num
            cur_num = sum
        uvm_root().logger.info("Fibonacci Sequence: " + str(fib_list))


class AluSeqItem(uvm_sequence_item):

    def __init__(self, name, aa, bb, op):
        super().__init__(name)
        self.A = aa
        self.B = bb
        self.op = Ops(op)

    def __eq__(self, other):
        same = self.A == other.A and self.B == other.B and self.op == other.op
        return same

    def __str__(self):
        return f"{self.get_name()} : A: 0x{self.A:02x} \
        OP: {self.op.name} ({self.op.value}) B: 0x{self.B:02x}"


class BaseSeq(uvm_sequence):

    async def body(self):
        for op in list(Ops):
            cmd_tr = AluSeqItem("cmd_tr", 0, 0, op)
            await self.start_item(cmd_tr)
            self.set_operands(cmd_tr)
            await self.finish_item(cmd_tr)

    def set_operands(self, tr):
        pass


class RandomSeq(BaseSeq):
    def set_operands(self, tr):
        tr.A = random.randint(0, 255)
        tr.B = random.randint(0, 255)


class MaxSeq(BaseSeq):
    def set_operands(self, tr):
        tr.A = 0xff
        tr.B = 0xff


class Driver(uvm_driver):
    def build_phase(self):
        self.ap = uvm_analysis_port("ap", self)

    def start_of_simulation_phase(self):
        self.bfm = TinyAluBfm()

    async def launch_tb(self):
        await self.bfm.reset()
        self.bfm.start_tasks()

    async def run_phase(self):
        await self.launch_tb()
        while True:
            cmd = await self.seq_item_port.get_next_item()
            await self.bfm.send_op(cmd.A, cmd.B, cmd.op)
            result = await self.bfm.get_result()
            self.ap.write(result)
            cmd.result = result
            self.seq_item_port.item_done()


class Coverage(uvm_subscriber):

    def start_of_simulation_phase(self):
        self.cvg = set()
        try:
            self.disable_errors = ConfigDB().get(
                self, "", "DISABLE_COVERAGE_ERRORS")
        except UVMConfigItemNotFound:
            self.disable_errors = False

    def write(self, cmd):
        (_, _, op) = cmd
        self.cvg.add(op)

    def report_phase(self):
        if not self.disable_errors:
            if len(set(Ops) - self.cvg) > 0:
                self.logger.error(
                    f"Functional coverage error. Missed: {set(Ops)-self.cvg}")
                assert False
            else:
                self.logger.info("Covered all operations")
                assert True


class Scoreboard(uvm_component):

    def build_phase(self):
        self.cmd_fifo = uvm_tlm_analysis_fifo("cmd_fifo", self)
        self.result_fifo = uvm_tlm_analysis_fifo("result_fifo", self)
        self.cmd_get_port = uvm_get_port("cmd_get_port", self)
        self.result_get_port = uvm_get_port("result_get_port", self)
        self.cmd_export = self.cmd_fifo.analysis_export
        self.result_export = self.result_fifo.analysis_export

    def connect_phase(self):
        self.cmd_get_port.connect(self.cmd_fifo.get_export)
        self.result_get_port.connect(self.result_fifo.get_export)

    def check_phase(self):
        while self.result_get_port.can_get():
            _, actual_result = self.result_get_port.try_get()
            cmd_success, cmd = self.cmd_get_port.try_get()
            if not cmd_success:
                self.logger.critical(f"result {actual_result} had no command")
            else:
                (A, B, op_numb) = cmd
                op = Ops(op_numb)
                predicted_result = alu_prediction(A, B, op)
                if predicted_result == actual_result:
                    self.logger.info(f"PASSED: 0x{A:02x} {op.name} 0x{B:02x} ="
                                     f" 0x{actual_result:04x}")
                else:
                    self.logger.error(f"FAILED: 0x{A:02x} {op.name} 0x{B:02x} "
                                      f"= 0x{actual_result:04x} "
                                      f"expected 0x{predicted_result:04x}")


class Monitor(uvm_component):
    def __init__(self, name, parent, method_name):
        super().__init__(name, parent)
        self.bfm = TinyAluBfm()
        self.get_method = getattr(self.bfm, method_name)

    def build_phase(self):
        self.ap = uvm_analysis_port("ap", self)

    async def run_phase(self):
        while True:
            datum = await self.get_method()
            self.logger.debug(f"MONITORED {datum}")
            self.ap.write(datum)


class AluEnv(uvm_env):

    def build_phase(self):
        self.seqr = uvm_sequencer("seqr", self)
        ConfigDB().set(None, "*", "SEQR", self.seqr)
        self.driver = Driver.create("driver", self)
        self.cmd_mon = Monitor("cmd_mon", self, "get_cmd")
        self.coverage = Coverage("coverage", self)
        self.scoreboard = Scoreboard("scoreboard", self)

    def connect_phase(self):
        self.driver.seq_item_port.connect(self.seqr.seq_item_export)
        self.cmd_mon.ap.connect(self.scoreboard.cmd_export)
        self.cmd_mon.ap.connect(self.coverage.analysis_export)
        self.driver.ap.connect(self.scoreboard.result_export)


@pyuvm.test()
class ParallelTest(AluTest):
    def end_of_elaboration_phase(self):
        uvm_factory().set_type_override_by_type(
            TestAllSeq, TestAllParallelSeq)
        return super().end_of_elaboration_phase()


@pyuvm.test()
class FibonacciTest(AluTest):
    def end_of_elaboration_phase(self):
        ConfigDB().set(None, "*", "DISABLE_COVERAGE_ERRORS", True)
        self.env.set_logging_level_hier(CRITICAL)
        uvm_factory().set_type_override_by_type(TestAllSeq, FibonacciSeq)
        return super().end_of_elaboration_phase()
