from pyuvm import *
import random
# All testbenches use tinyalu_utils, so store it in a central
# place and add its path to the sys path so we can import it
import sys
from pathlib import Path
sys.path.append(str(Path("..").resolve()))
from tinyalu_utils import TinyAluBfm, Ops, alu_prediction  # noqa: E402


class AluSeqItem(uvm_sequence_item):

    def __init__(self, name, aa, bb, op):
        super().__init__(name)
        self.A = aa
        self.B = bb
        self.op = Ops(op)

    def randomize_operands(self):
        self.A = random.randint(0, 255)
        self.B = random.randint(0, 255)

    def randomize(self):
        self.randomize_operands()
        self.op = random.choice(list(Ops))

    def __eq__(self, other):
        same = self.A == other.A and self.B == other.B and self.op == other.op
        return same

    def __str__(self):
        return f"{self.get_name()} : A: 0x{self.A:02x} \
        OP: {self.op.name} ({self.op.value}) B: 0x{self.B:02x}"


class AluResultItem(uvm_sequence_item):
    def __init__(self, name, result):
        super().__init__(name)
        self.result = result

    def __str__(self):
        return f"RESULT: {self.result}"


class Driver(uvm_driver):
    def build_phase(self):
        self.ap = uvm_analysis_port("ap", self)

    def start_of_simulation_phase(self):
        self.bfm = self.cdb_get("BFM")

    async def launch_tb(self):
        await self.bfm.reset()
        await self.bfm.start_bfms()

    async def run_phase(self):
        await self.launch_tb()
        while True:
            cmd = await self.seq_item_port.get_next_item()
            await self.bfm.send_op(cmd.A, cmd.B, cmd.op)
            result = await self.bfm.get_result()
            self.ap.write(result)
            cmd.result = result
            self.seq_item_port.item_done()


class ResponseDriver(Driver):
    async def run_phase(self):
        await self.launch_tb()
        while True:
            cmd = await self.seq_item_port.get_next_item()
            await self.bfm.send_op(cmd.A, cmd.B, cmd.op)
            result = await self.bfm.get_result()
            self.ap.write(result)
            result_item = AluResultItem("result_item", result)
            result_item.set_id_info(cmd)
            self.seq_item_port.item_done(result_item)


class Coverage(uvm_subscriber):

    def end_of_elaboration_phase(self):
        self.cvg = set()
        try:
            self.disable_errors = ConfigDB().get(self, "", "DISABLE_COVERAGE_ERRORS")
        except UVMConfigItemNotFound:
            self.disable_errors = False

    def write(self, cmd):
        (_, _, op) = cmd
        self.cvg.add(op)

    def report_phase(self):
        if len(set(Ops) - self.cvg) > 0:
            self.logger.error(
                f"Functional coverage error. Missed: {set(Ops)-self.cvg}")
            assert self.disable_errors or False
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
        self.bfm = self.cdb_get("BFM")
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


class FibonacciSeq(uvm_sequence):
    async def body(self):
        prev_num = 0
        cur_num = 1
        fib_list = [prev_num, cur_num]
        cmd = AluSeqItem("cmd", None, None, Ops.ADD)
        for _ in range(7):
            await self.start_item(cmd)
            cmd.A = prev_num
            cmd.B = cur_num
            await self.finish_item(cmd)
            fib_list.append(cmd.result)
            prev_num = cur_num
            cur_num = cmd.result
        logger = ConfigDB().get(None, "", "LOGGER")
        logger.info("Fibonacci Sequence: " + str(fib_list))


class ResponseFibSeq(uvm_sequence):
    async def body(self):
        prev_num = 0
        cur_num = 1
        fib_list = [prev_num, cur_num]
        cmd = AluSeqItem("cmd", None, None, Ops.ADD)
        for _ in range(7):
            await self.start_item(cmd)
            cmd.A = prev_num
            cmd.B = cur_num
            await self.finish_item(cmd)
            rsp = await self.get_response()
            fib_list.append(rsp.result)
            prev_num = cur_num
            cur_num = rsp.result
        logger = ConfigDB().get(None, "", "LOGGER")
        logger.info("Fibonacci Sequence: " + str(fib_list))


class FibonacciTest(uvm_test):
    def build_phase(self):
        self.env = AluEnv("env", self)

    def end_of_elaboration_phase(self):
        self.seqr = ConfigDB().get(self, "", "SEQR")
        ConfigDB().set(None, "*", "LOGGER", self.logger)
        self.env.set_logging_level_hier(CRITICAL)
        ConfigDB().set(None, "*", "DISABLE_COVERAGE_ERRORS", True)

    async def run_phase(self):
        self.raise_objection()
        seq = FibonacciSeq.create("seq")
        await seq.start(self.seqr)
        self.drop_objection()


class ResponseFibTest(FibonacciTest):
    def build_phase(self):
        uvm_factory().set_type_override_by_type(Driver, ResponseDriver)
        uvm_factory().set_type_override_by_type(FibonacciSeq, ResponseFibSeq)
        super().build_phase()


@cocotb.test()
async def fibonacci_test(dut):
    """Run Fibonacci sequence"""
    bfm = TinyAluBfm(dut)
    ConfigDB().set(None, "*", "BFM", bfm)
    await uvm_root().run_test("FibonacciTest")


@cocotb.test()
async def response_fib_test(dut):
    """Show get_response"""
    bfm = TinyAluBfm(dut)
    ConfigDB().set(None, "*", "BFM", bfm)
    await uvm_root().run_test("ResponseFibTest")
