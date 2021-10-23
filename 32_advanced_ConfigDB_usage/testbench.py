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
        self.np = NumberPrinter("np", self)
        ConfigDB().set(self, "np", "NUMB", 42)


class NumberTest(uvm_test):
    def build_phase(self):
        self.env = NumberEnv("env", self)
        ConfigDB().set(self, "env.np", "NUMB", 21)

    def end_of_elaboration_phase(self):
        self.logger.info(str(ConfigDB()))


class WildCardTest(NumberTest):
    def build_phase(self):
        self.env = NumberEnv("env", self)
        ConfigDB().set(None, "*", "NUMB", 21)


@cocotb.test()
async def test_component(_):
    """Demonstrate no num in config"""
    await uvm_root().run_test("NumberPrinter")


@cocotb.test()
async def test_env(_):
    """Demonstrate printing a number"""
    await uvm_root().run_test("NumberEnv")


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
    await uvm_root().run_test("NumberTest")


@cocotb.test()
async def wildcard_test(_):
    """Demonstrate tracing"""
    ConfigDB().clear()
    ConfigDB().is_tracing = True
    await uvm_root().run_test("WildCardTest")
