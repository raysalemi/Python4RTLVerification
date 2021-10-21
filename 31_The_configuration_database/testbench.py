import cocotb
from pyuvm import *


class MsgLogger(uvm_component):

    def build_phase(self):
        self.msg = ConfigDB().get(self, "", "MSG")

    async def run_phase(self):
        self.raise_objection()
        self.logger.info(self.msg)
        self.drop_objection()


class MsgEnv(uvm_env):
    def build_phase(self):
        self.loga = MsgLogger("loga", self)
        self.logb = MsgLogger("logb", self)


class LogTest(uvm_test):

    def build_phase(self):
        self.env = MsgEnv("env", self)
        ConfigDB().set(self, "env.loga", "MSG", "loga msg")
        ConfigDB().set(self, "env.logb", "MSG", "logb msg")


@cocotb.test()
async def name_myself(dut):
    """Exercise hierarchy naming"""
    await uvm_root().run_test("LogTest")
    assert True
