#!/usr/bin/env python
# coding: utf-8

# # The TinyALU TLM Testbench

# In[1]:

from tb_pkg import *
from pyuvm import *


class AluSeqItem(uvm_sequence_item):

    def __init__(self, name, A=0, B=0, op=Ops.ADD):
        super().__init__(name)
        self.A = A
        self.B = B
        self.op = Ops(op)

    def __eq__(self, other):
        same = self.A == other.A                and self.B == other.B                and self.op == other.op
        return same

    def __str__(self):
        return f"{self.get_name()} : A: 0x{self.A:02x} OP: {self.op.name} ({self.op.value}) B: 0x{self.B:02x}"
    
    def randomize(self):
        self.A = random.randint(0,255)
        self.B = random.randint(0,255)
        self.op = random.choice(list(Ops))
        
class AluSeq(uvm_sequence):
    def body(self):
        for _ in range(5):
            cmd_tr = AluSeqItem("cmd_tr")
            self.start_item(cmd_tr) 
            cmd_tr.randomize()
            self.finish_item(cmd_tr) 
            

class Driver(uvm_driver):
    def build_phase(self):
        self.bfm = self.cdb_get("BFM")

    def run_phase(self):
        while not ObjectionHandler().run_phase_complete():
            command = self.seq_item_port.get_next_item()
            self.bfm.send_op(command.A, command.B, command.op)
            self.logger.debug(f"Sent command: {command}")
            time.sleep(0.5)
            self.seq_item_port.item_done()


class Coverage(uvm_subscriber):
    
    def end_of_elaboration_phase(self):
        self.cvg = set()
    
    def write(self, cmd):
        (_, _, op) = cmd
        self.cvg.add(op)

    def check_phase(self):
        if len(set(Ops) - self.cvg) > 0:
            self.logger.error(f"Functional coverage error. Missed: {set(Ops)-self.cvg}")


class Scoreboard(uvm_component):  

    def build_phase(self):
        self.cmd_fifo = uvm_tlm_analysis_fifo("cmd_fifo", self)
        self.rslt_fifo = uvm_tlm_analysis_fifo("rslt_fifo", self)
        self.cmd_get_port = uvm_get_port("cmd_get_port", self)    
        self.rslt_get_port = uvm_get_port("rslt_get_port", self) 
        self.cmd_export = self.cmd_fifo.analysis_export
        self.rslt_export = self.rslt_fifo.analysis_export

    def connect_phase(self):
        self.cmd_get_port.connect(self.cmd_fifo.get_export)
        self.rslt_get_port.connect(self.rslt_fifo.get_export)

    def check_phase(self):
        while self.rslt_get_port.can_get():
            _, actual_result = self.rslt_get_port.try_get()
            cmd_success, (A, B, op_numb) = self.cmd_get_port.try_get()
            if not cmd_success:
                self.logger.critical(f"result {actual_result} had no command")
            else:
                op = Ops(op_numb)
                predicted_result = TlmAluBfm.alu_op(A, B, op)
                if predicted_result == actual_result:
                    self.logger.info(f"PASSED: 0x{A:02x} {op.name} 0x{B:02x} ="
                                     f" 0x{actual_result:04x}")
                else:
                    self.logger.error(f"FAILED: 0x{A:02x} {op.name} 0x{B:02x} "
                                      f"= 0x{actual_result:04x} expected 0x{predicted_result:04x}")


class Monitor(uvm_component):
    def __init__(self, name, parent, method_name):
        super().__init__(name, parent)
        self.method_name = method_name
    
    def build_phase(self):
        self.bfm = self.cdb_get("BFM")
        self.ap = uvm_analysis_port("ap", self)

    def run_phase(self):
        while not ObjectionHandler().run_phase_complete():
            get_method = getattr(self.bfm, self.method_name)
            datum = get_method()
            self.ap.write(datum)    


class AluEnv(uvm_env):

    def build_phase(self):
        self.cmd_mon = Monitor("cmd_mon", self, "get_cmd")
        self.rslt_mon = Monitor("rslt_mon", self, "get_result")
        self.scoreboard = Scoreboard("scoreboard", self)
        self.coverage = Coverage("coverage", self)
        self.driver = Driver("driver", self)
        self.seqr = uvm_sequencer("seqr", self)
        ConfigDB().set(None, "*", "SEQR", self.seqr)
        ConfigDB().set(None, "*", "CVG", self.coverage)
        
    def connect_phase(self):
        self.cmd_mon.ap.connect(self.scoreboard.cmd_export)
        self.cmd_mon.ap.connect(self.coverage)
        self.rslt_mon.ap.connect(self.scoreboard.rslt_export)
        self.driver.seq_item_port.connect(self.seqr.seq_item_export)


class TlmAluEnv(AluEnv):
    def build_phase(self):
        super().build_phase()
        self.bfm = TlmAluBfm("BFM", self)
        ConfigDB().set(None, "*", "BFM", self.bfm)


class CocotbAluEnv(AluEnv):
    def build_phase(self):
        super().build_phase()
        self.bfm = self.cdb_get("BFM")


class BaseTest(uvm_test):
    def build_phase(self):
        self.env = AluEnv.create("env", self)

    def run_phase(self):
        self.raise_objection()
        seqr = ConfigDB().get(self, "", "SEQR")
        seq = AluSeq("seq")
        seq.start(seqr)
        time.sleep(1)
        self.drop_objection()

    def end_of_elaboration_phase(self):
        self.set_logging_level_hier(logging.DEBUG)


class TlmTest(BaseTest):
    def build_phase(self):
        uvm_factory().set_type_override_by_type(AluEnv, TlmAluEnv)
        super().build_phase()


class CocotbTest(BaseTest):
    def build_phase(self):
        uvm_factory().set_type_override_by_type(AluEnv, CocotbAluEnv)
        super().build_phase()

    def final_phase(self):
        bfm = self.cdb_get("BFM")
        bfm.done.set()

if __name__ == "__main__":
    uvm_root().run_test("TlmTest")

