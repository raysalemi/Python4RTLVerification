import pyuvm
from pyuvm import *


#  ## The ConfigDB().get method

# Figure 1: Logging a message we get from the ConfigDB
class MsgLogger(uvm_component):

    async def run_phase(self):
        self.raise_objection()
        msg = ConfigDB().get(self, "", "MSG")
        self.logger.info(msg)
        self.drop_objection()


# ## The ConfigDB().set() method

# Figure 2: Instantiating two loggers in the environment
class MsgEnv(uvm_env):
    def build_phase(self):
        self.loga = MsgLogger("loga", self)
        self.logb = MsgLogger("logb", self)


# Figure 3: Giving loga and logb different messages
@pyuvm.test()
class MsgTest(uvm_test):

    def build_phase(self):
        self.env = MsgEnv("env", self)
        ConfigDB().set(self, "env.loga", "MSG", "LOG A msg")
        ConfigDB().set(self, "env.logb", "MSG", "LOG B msg")


# ## Wildcards
# Figure 5: Adding talka and talkb to the environment

class MultiMsgEnv(MsgEnv):
    def build_phase(self):
        self.talka = MsgLogger("talka", self)
        self.talkb = MsgLogger("talkb", self)
        super().build_phase()


# Figure 6: Using a wildcard to store a message
@pyuvm.test()
class MultiMsgTest(uvm_test):
    def build_phase(self):
        self.env = MultiMsgEnv("env", self)
        ConfigDB().set(self, "env.loga", "MSG", "LOG A msg")
        ConfigDB().set(self, "env.logb", "MSG", "LOG B msg")
        ConfigDB().set(self, "env.t*", "MSG", "TALK TALK")


# ## Global data
# Figure 9: Adding the gtalk component to the environment
class GlobalEnv(MultiMsgEnv):
    def build_phase(self):
        self.gtalk = MsgLogger("gtalk", self)
        super().build_phase()


# Figure 10: Storing a global message
@pyuvm.test()
class GlobalTest(uvm_test):
    def build_phase(self):
        self.env = GlobalEnv("env", self)
        ConfigDB().set(self, "env.loga", "MSG", "LOG A msg")
        ConfigDB().set(self, "env.logb", "MSG", "LOG B msg")
        ConfigDB().set(self, "env.t*", "MSG", "TALK TALK")
        ConfigDB().set(None, "*", "MSG", "GLOBAL")


# ## Parent/child conflict

# Figure 12: Creating a ConfigDB conflict between
# parent and child at env.loga.  Which message prints?
class ConflictEnv(uvm_env):
    def build_phase(self):
        self.loga = MsgLogger("loga", self)
        ConfigDB().set(self, "loga", "MSG", "CHILD RULES!")


@pyuvm.test()
class ConflictTest(uvm_test):
    def build_phase(self):
        self.env = ConflictEnv("env", self)
        ConfigDB().set(self, "env.loga", "MSG", "PARENT RULES!")
