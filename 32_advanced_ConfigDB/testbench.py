import cocotb
from pyuvm import *


class NumberPrinter(uvm_component):
    def build_phase(self):
        try:
            self.num = ConfigDB().get(self, "", "NUMB")
        except UVMConfigItemNotFound:
            self.num = None

    async def run_phase(self):
        self.raise_objection()
        self.logger.info(f"NUM: {self.num}")
        self.drop_objection()


class NumberEnv(uvm_env):
    def build_phase(self):
        ConfigDB().set(self, "np", "NUMB", 42)
        self.logger.info(str(ConfigDB()))
        self.np = NumberPrinter("np", self)


class WildCardEnv(uvm_env):
    def build_phase(self):
        ConfigDB().set(self, "*", "NUMB", 42)
        self.logger.info(str(ConfigDB()))
        self.np = NumberPrinter("np", self)


class NumberTest(uvm_test):
    def build_phase(self):
        self.env = NumberEnv("env", self)
        ConfigDB().set(self, "env.np", "NUMB", 21)


class WildcardEnvTest(uvm_test):
    def build_phase(self):
        self.env = WildCardEnv("env", self)


class LogTest(uvm_test):
    async def run_phase(self):
        self.raise_objection()
        config_db_str = str(ConfigDB())
        self.logger.info(config_db_str)
        self.drop_objection()


class WildCardTest(NumberTest):
    def build_phase(self):
        self.env = NumberEnv("env", self)
        ConfigDB().set(None, "*", "NUMB", 21)


@cocotb.test()
async def print_configdb(_):
    """Demonstrate printing the ConfigDB"""
    ConfigDB().set(None, "*", "NUMB", 15)
    print(ConfigDB())


@cocotb.test()
async def log_configdb(_):
    """Demonstrate logging the ConfigDB"""
    ConfigDB().set(None, "*", "NUMB", 15)
    await uvm_root().run_test("LogTest")


@cocotb.test()
async def trace_configdb(_):
    """Demonstrate logging the ConfigDB"""
    ConfigDB().is_tracing = True
    ConfigDB().set(None, "*", "NUMB", 15)
    await uvm_root().run_test("NumberPrinter")


@cocotb.test()
async def test_env(_):
    """Demonstrate instantiating comp"""
    ConfigDB().is_tracing = False
    ConfigDB().clear()
    await uvm_root().run_test("NumberEnv")


@cocotb.test()
async def test_env_wc(_):
    """Demonstrate global wildcard"""
    ConfigDB().is_tracing = False
    ConfigDB().clear()
    ConfigDB().set(None, "*", "NUMB", -99)
    await uvm_root().run_test("NumberEnv")


@cocotb.test()
async def wc_env_test(_):
    """Demonstrate component wildcard"""
    ConfigDB().is_tracing = False
    ConfigDB().clear()
    ConfigDB().set(None, "*", "NUMB", 222)
    await uvm_root().run_test("WildcardEnvTest")


@cocotb.test()
async def test_test(_):
    """Demonstrate printing a number using a test"""
    ConfigDB().clear()
    await uvm_root().run_test("NumberTest")


@cocotb.test()
async def trace_test(_):
    """Demonstrate tracing"""
    ConfigDB().clear()
    ConfigDB().is_tracing = True
    await uvm_root().run_test("NumberPrinter")


@cocotb.test()
async def wildcard_test(_):
    """Demonstrate tracing"""
    ConfigDB().clear()
    ConfigDB().is_tracing = True
    await uvm_root().run_test("WildCardTest")
