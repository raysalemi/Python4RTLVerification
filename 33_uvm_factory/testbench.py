import cocotb
from pyuvm import *
from pathlib import Path
import sys
# All testbenches use tinyalu_utils, so store it in a central
# place and add its path to the sys path so we can import it
sys.path.append(str(Path("..").resolve()))


# # uvm_factory
# ## The create() method
class TinyComponent(uvm_component):
    async def run_phase(self):
        self.raise_objection()
        self.logger.info("I'm so tiny!")
        self.drop_objection()


class TinyTest(uvm_test):
    def build_phase(self):
        self.tc = TinyComponent("tc", self)


@cocotb.test()
async def tiny_test(_):
    await uvm_root().run_test("TinyTest")


class TinyFactoryTest(uvm_test):
    def build_phase(self):
        self.tc = TinyComponent.create("tc", self)


@cocotb.test()
async def tiny_factory_test(_):
    await uvm_root().run_test("TinyFactoryTest")


# ## Creating objects with uvm_factory()
class CreateTest(uvm_test):
    def build_phase(self):
        self.tc = uvm_factory().create_component_by_name(
            "TinyComponent",
            name="tc", parent=self)


@cocotb.test()
async def create_test(_):
    """Create a component using factory"""
    uvm_factory().clear_overrides()
    await uvm_root().run_test("CreateTest")


# ## Overriding types
class MediumComponent(uvm_component):
    async def run_phase(self):
        self.raise_objection()
        self.logger.info("I'm medium size.")
        self.drop_objection()


class MediumFactoryTest(TinyFactoryTest):
    def build_phase(self):
        uvm_factory().set_type_override_by_type(
            TinyComponent, MediumComponent)
        super().build_phase()


@cocotb.test()
async def medium_factory_test(_):
    await uvm_root().run_test("MediumFactoryTest")


class MediumNameTest(TinyFactoryTest):
    def build_phase(self):
        uvm_factory().set_type_override_by_name(
            "TinyComponent", "MediumComponent")
        super().build_phase()


@cocotb.test()
async def medium_name_test(_):
    await uvm_root().run_test("MediumNameTest")


# ## Factory overrides by instance
class TwoCompEnv(uvm_env):
    def build_phase(self):
        self.tc1 = TinyComponent.create("tc1", self)
        self.tc2 = TinyComponent.create("tc2", self)


class TwoCompTest(uvm_test):
    def build_phase(self):
        uvm_factory().set_inst_override_by_type(
            TinyComponent, MediumComponent, "uvm_test_top.env.tc1")
        self.env = TwoCompEnv("env", self)


@cocotb.test()
async def two_comp_test(_):
    uvm_factory().clear_overrides()
    await uvm_root().run_test(TwoCompTest)


# ## Debugging the uvm_factory()
class PrintOverrides(MediumNameTest):
    def final_phase(self):
        uvm_factory().print(0)


@cocotb.test()
async def print_overrides(_):
    await uvm_root().run_test(PrintOverrides)


class PrintInstanceOverrides(TwoCompTest):
    def final_phase(self):
        uvm_factory().print(0)


@cocotb.test()
async def print_inst_overrides(_):
    await uvm_root().run_test(PrintInstanceOverrides)


# ### Logging uvm_factory() data
class LoggingOverrides(MediumNameTest):
    def final_phase(self):
        uvm_factory().debug_level = 0
        factory_log = "\n"+str(uvm_factory())
        self.logger.info(factory_log)


@cocotb.test()
async def log_overrides(_):
    await uvm_root().run_test(LoggingOverrides)
