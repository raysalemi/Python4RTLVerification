from pyuvm import *
from tb_pkg import *
import random

class Driver(uvm_component):
    def build_phase(self):
        self.dut = self.cdb_get("DUT")
    
    def run_phase(self):
        self.raise_objection()
        for _ in range(5):
            A = random.randrange(256)
            B = random.randrange(256)
            op = random.choice(list(Ops))
            cmd = AluCommand("cmd", A, B, op)
            self.dut.send_op(cmd)
        time.sleep(1) # Wait for last operation to complete
        self.drop_objection()        

class Coverage(uvm_subscriber):
    
    def end_of_elaboration_phase(self):
        self.cvg = set()
        self.received_data = False
    
    def write(self, cmd):
        self.cvg.add(cmd.op)
        self.received_data = True

    def check_phase(self):
        if self.received_data and len(set(Ops) - self.cvg) > 0:
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

    def run_phase(self):
        while True:
            rtxn = self.rslt_get_port.get()
            cmd = self.cmd_get_port.get()  
            actual_result = rtxn.result
            predicted_result = TinyAluTlm.alu_op(cmd.A, cmd.B, cmd.op)
            if predicted_result == actual_result:
                self.logger.info(f"PASSED: 0x{cmd.A:02x} {cmd.op.name} 0x{cmd.B:02x} ="
                                 f" 0x{actual_result:04x}")
            else:
                self.logger.error(f"FAILED: 0x{cmd.A:02x} {cmd.op.name} 0x{cmd.B:02x} "
                                  f"= 0x{actual_result:04x} expected 0x{predicted_result:04x}")     

                
class Monitor(uvm_component):
    def __init__(self, name, parent, method_name):
        super().__init__(name, parent)
        self.method_name = method_name
    
    def build_phase(self):
        self.dut = self.cdb_get("DUT")
        self.ap = uvm_analysis_port("ap", self)

    def run_phase(self):
        while True:
            get_method = getattr(self.dut, self.method_name)
            datum = get_method()
            self.ap.write(datum)    

class AluAgent(uvm_agent):
    def build_phase(self):
        super().build_phase()
        if self.active():
            self.driver = Driver.create("driver", self)

        self.scoreboard = Scoreboard.create("scoreboard", self)
        self.coverage = Coverage.create("coverage", self)

    def connect_phase(self):
        self.cmd_export  = self.scoreboard.cmd_export
        self.rslt_export = self.scoreboard.result_export
        self.cvg_export = self.coverage

class AluEnv(uvm_env):

    def build_phase(self):
        self.cmd_mon = Monitor("cmd_mon", self, "get_cmd")
        self.rslt_mon = Monitor("rslt_mon", self, "get_result")    
        
        # active agent drives stimulus, passive agent monitors it
        self.cdb_set("is_active", uvm_active_passive_enum.UVM_ACTIVE,
                     inst_path="active*")
        self.cdb_set("is_active", uvm_active_passive_enum.UVM_PASSIVE,
                     inst_path="passive*")
        self.active_agent = AluAgent("active_agent", self)
        self.passive_agent = AluAgent("passive_agent", self)        

    def connect_phase(self):
        # For scoreboard
        self.cmd_mon.ap.connect(self.passive_agent.cmd_export)
        self.rslt_mon.ap.connect(self.passive_agent.rslt_export)
        # For coverage
        self.cmd_mon.ap.connect(self.passive_agent.cvg_export)
        
class AluTest(uvm_test):
    def build_phase(self):
        self.dut = TinyAluTlm("dut", self)
        self.cdb_set("DUT", self.dut)
        self.env = AluEnv("env", self)
