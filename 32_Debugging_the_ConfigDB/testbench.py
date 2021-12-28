import cocotb
from pyuvm import *


#  # Debugging the ConfigDB()
#  ## Missing Data

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


@cocotb.test(expect_error=UVMConfigItemNotFound)
async def log_msgs(_):
    await uvm_root().run_test(MsgTest)


# ## Catching Exceptions
class MsgTestAlmostFixed(uvm_test):

    def build_phase(self):
        self.env = MsgEnv("env", self)
        ConfigDB().set(self, "env.loga", "MSG", "LOG A msg")
        ConfigDB().set(self, "env.logb", "MESG", "LOG B msg")


@cocotb.test(expect_error=UVMConfigItemNotFound)
async def log_msgs_almost(_):
    await uvm_root().run_test(MsgTestAlmostFixed)


class NiceMsgLogger(uvm_component):

    async def run_phase(self):
        self.raise_objection()
        try:
            msg = ConfigDB().get(self, "", "MSG")
        except UVMConfigItemNotFound:
            self.logger.warning("Could not find MSG. Setting to default")
            msg = "No message for you!"
        self.logger.info(msg)
        self.drop_objection()


class NiceMsgEnv(uvm_env):
    def build_phase(self):
        self.loga = NiceMsgLogger("loga", self)
        self.logb = NiceMsgLogger("logb", self)


# ## Printing the ConfigDB
class NiceMsgTest(uvm_test):

    def build_phase(self):
        self.env = NiceMsgEnv("env", self)
        ConfigDB().set(self, "env.loga", "MSG", "LOG A msg")

    def end_of_elaboration_phase(self):
        print(ConfigDB())


@cocotb.test()
async def nice_log_msgs(_):
    await uvm_root().run_test(NiceMsgTest)


class NiceMsgTestAlmostFixed(uvm_test):

    def build_phase(self):
        self.env = NiceMsgEnv("env", self)
        ConfigDB().set(self, "env.loga", "MSG", "LOG A msg")
        ConfigDB().set(self, "env.logb", "MESG", "LOG B msg")

    def end_of_elaboration_phase(self):
        print(ConfigDB())


@cocotb.test()
async def nice_log_msgs_almost(_):
    await uvm_root().run_test(NiceMsgTestAlmostFixed)
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


# ## Debugging Parent/child conflict
class ConflictEnv(uvm_env):
    def build_phase(self):
        self.loga = MsgLogger("loga", self)
        ConfigDB().set(self, "loga", "MSG", "CHILD RULES!")


class ConflictTest(uvm_test):
    def build_phase(self):
        self.env = ConflictEnv("env", self)
        ConfigDB().set(self, "env.loga", "MSG", "PARENT RULES!")

    def end_of_elaboration_phase(self):
        print(ConfigDB())


@cocotb.test()
async def conflict_test(_):
    await uvm_root().run_test(ConflictTest)


# ## Tracing ConfigDB() Operations
class GlobalEnv(MultiMsgEnv):
    def build_phase(self):
        self.gtalk = MsgLogger("gtalk", self)
        super().build_phase()


class GlobalTest(uvm_test):
    def build_phase(self):
        ConfigDB().is_tracing = True
        self.env = GlobalEnv("env", self)
        ConfigDB().set(self, "env.loga", "MSG", "LOG A msg")
        ConfigDB().set(self, "env.logb", "MSG", "LOG B msg")
        ConfigDB().set(self, "env.t*", "MSG", "TALK TALK")
        ConfigDB().set(None, "*", "MSG", "GLOBAL")


@cocotb.test()
async def global_msg(_):
    await uvm_root().run_test(GlobalTest)
