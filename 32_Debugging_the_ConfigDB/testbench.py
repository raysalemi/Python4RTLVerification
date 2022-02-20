import pyuvm
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

# Figure 1: Instantiate two loggers

class MsgEnv(uvm_env):
    def build_phase(self):
        self.loga = MsgLogger("loga", self)
        self.logb = MsgLogger("logb", self)


# Figure 2: Provide a message for only one logger
@pyuvm.test(expect_error=UVMConfigItemNotFound)
class MsgTest(uvm_test):

    def build_phase(self):
        self.env = MsgEnv("env", self)
        ConfigDB().set(self, "env.loga", "MSG", "LOG A msg")


# ## Catching Exceptions
# Figure 3: Misspelling a ConfigDB() key
@pyuvm.test(expect_error=UVMConfigItemNotFound)
class MsgTestAlmostFixed(uvm_test):

    def build_phase(self):
        self.env = MsgEnv("env", self)
        ConfigDB().set(self, "env.loga", "MSG", "LOG A msg")
        ConfigDB().set(self, "env.logb", "MESG", "LOG B msg")


# Figure 4: Catching ConfigDB()exceptions
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

# Figure 6: Printing the ConfigDB()
@pyuvm.test()
class NiceMsgTest(uvm_test):

    def build_phase(self):
        self.env = NiceMsgEnv("env", self)
        ConfigDB().set(self, "env.loga", "MSG", "LOG A msg")

    def end_of_elaboration_phase(self):
        print(ConfigDB())


# Figure 7: Debugging a ConfigDB() error using print()
@pyuvm.test()
class NiceMsgTestAlmostFixed(uvm_test):

    def build_phase(self):
        self.env = NiceMsgEnv("env", self)
        ConfigDB().set(self, "env.loga", "MSG", "LOG A msg")
        ConfigDB().set(self, "env.logb", "MESG", "LOG B msg")

    def end_of_elaboration_phase(self):
        print(ConfigDB())


# ## Wildcards

class MultiMsgEnv(MsgEnv):
    def build_phase(self):
        self.talka = MsgLogger("talka", self)
        self.talkb = MsgLogger("talkb", self)
        super().build_phase()


@pyuvm.test()
class MultiMsgTest(uvm_test):
    def build_phase(self):
        self.env = MultiMsgEnv("env", self)
        ConfigDB().set(self, "env.loga", "MSG", "LOG A msg")
        ConfigDB().set(self, "env.logb", "MSG", "LOG B msg")
        ConfigDB().set(self, "env.t*", "MSG", "TALK TALK")


# ## Debugging Parent/child conflict
class ConflictEnv(uvm_env):
    def build_phase(self):
        self.loga = MsgLogger("loga", self)
        ConfigDB().set(self, "loga", "MSG", "CHILD RULES!")


# Figure 8: Both parent and child reference env.loga
@pyuvm.test()
class ConflictTest(uvm_test):
    def build_phase(self):
        self.env = ConflictEnv("env", self)
        ConfigDB().set(self, "env.loga", "MSG", "PARENT RULES!")

    def end_of_elaboration_phase(self):
        print(ConfigDB())


# ## Tracing ConfigDB() Operations
class GlobalEnv(MultiMsgEnv):
    def build_phase(self):
        self.gtalk = MsgLogger("gtalk", self)
        super().build_phase()


# Figure 10: Tracing ConfigDB() operations using is_tracing
@pyuvm.test()
class GlobalTest(uvm_test):
    def build_phase(self):
        ConfigDB().is_tracing = True
        self.env = GlobalEnv("env", self)
        ConfigDB().set(self, "env.loga", "MSG", "LOG A msg")
        ConfigDB().set(self, "env.logb", "MSG", "LOG B msg")
        ConfigDB().set(self, "env.t*", "MSG", "TALK TALK")
        ConfigDB().set(None, "*", "MSG", "GLOBAL")
