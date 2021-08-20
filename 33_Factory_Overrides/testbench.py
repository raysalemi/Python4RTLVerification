import cocotb
from pyuvm import *


class Producer(uvm_component):
    def build_phase(self):
        self.ap = uvm_analysis_port("ap", self)

    async def run_phase(self):
        self.raise_objection()
        for nn in range(3):
            self.ap.write(nn)
        self.drop_objection()


class Consumer(uvm_subscriber):

    def write(self, datum):
        print(f"{self.get_name()}: {datum}", end=" ")


class Env(uvm_env):
    def build_phase(self):
        self.pro = Producer.create("pro", self)
        self.con1 = Consumer.create("con1", self)
        self.con2 = Consumer.create("con2", self)

    def connect_phase(self):
        self.pro.ap.connect(self.con1)
        self.pro.ap.connect(self.con2)


class VertConsumer(Consumer):
    def write(self, datum):
        print(f"{self.get_name()}: {datum}")


class IncConsumer(VertConsumer):
    def write(self, datum):
        print(f"{self.get_name()}: {datum+1}")


class BaseTest(uvm_test):
    def build_phase(self):
        self.env = Env.create("env", self)


class VertTest(BaseTest):
    def build_phase(self):
        uvm_factory().set_type_override_by_type(Consumer, VertConsumer)
        super().build_phase()


class IncTest(BaseTest):
    def build_phase(self):
        uvm_factory().set_inst_override_by_type(Consumer, IncConsumer, self.get_full_name() + ".env.con2")
        super().build_phase()


@cocotb.test()
async def overrides(dut):
    """Testing factory overrides"""
    await uvm_root().run_test("BaseTest")
    await uvm_root().run_test("VertTest")
    await uvm_root().run_test("IncTest")
    assert True
