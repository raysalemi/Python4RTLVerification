import cocotb
from pyuvm import *


#  ## The ConfigDB().get method

class MsgLogger(uvm_component):

    async def run_phase(self):
        self.raise_objection()
        msg = ConfigDB().get(self, "", "MSG")
        self.logger.info(msg)
        self.drop_objection()


# ## The ConfigDB().set() method

class MsgEnv(uvm_env):
    def build_phase(self):
        self.loga = MsgLogger("loga", self)
        self.logb = MsgLogger("logb", self)


class MsgTest(uvm_test):

    def build_phase(self):
        self.env = MsgEnv("env", self)
        ConfigDB().set(self, "env.loga", "MSG", "LOG A msg")
        ConfigDB().set(self, "env.logb", "MSG", "LOG B msg")


@cocotb.test()
async def log_msgs(dut):
    await uvm_root().run_test(MsgTest)


# ## Wildcards
class MultiMsgEnv(MsgEnv):
    def build_phase(self):
        self.talka = MsgLogger("talka", self)
        self.talkb = MsgLogger("talkb", self)
        super().build_phase()


class MultiMsgTest(uvm_test):
    def build_phase(self):
        self.env = MultiMsgEnv("env", self)
        ConfigDB().set(self, "env.loga", "MSG", "LOG A msg")
        ConfigDB().set(self, "env.logb", "MSG", "LOG B msg")
        ConfigDB().set(self, "env.t*", "MSG", "TALK TALK")


@cocotb.test()
async def multi_msg(_):
    await uvm_root().run_test(MultiMsgTest)


# ## Global data
class GlobalEnv(MultiMsgEnv):
    def build_phase(self):
        self.gtalk = MsgLogger("gtalk", self)
        super().build_phase()


class GlobalTest(uvm_test):
    def build_phase(self):
        self.env = GlobalEnv("env", self)
        ConfigDB().set(self, "env.loga", "MSG", "LOG A msg")
        ConfigDB().set(self, "env.logb", "MSG", "LOG B msg")
        ConfigDB().set(self, "env.t*", "MSG", "TALK TALK")
        ConfigDB().set(None, "*", "MSG", "GLOBAL")


@cocotb.test()
async def global_msg(_):
    await uvm_root().run_test(GlobalTest)


# ## Parent/child conflict
class ConflictEnv(uvm_env):
    def build_phase(self):
        self.loga = MsgLogger("loga", self)
        ConfigDB().set(self, "loga", "MSG", "CHILD RULES!")


class ConflictTest(uvm_test):
    def build_phase(self):
        self.env = ConflictEnv("env", self)
        ConfigDB().set(self, "env.loga", "MSG", "PARENT RULES!")


@cocotb.test()
async def conflict_test(_):
    await uvm_root().run_test(ConflictTest)
