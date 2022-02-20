import pyuvm
from pyuvm import *


# # uvm_factory
# ## The create() method
# Figure 1: A tiny example component
class TinyComponent(uvm_component):
    async def run_phase(self):
        self.raise_objection()
        self.logger.info("I'm so tiny!")
        self.drop_objection()


# Figure 2: Instantiating the component by calling the class directly
@pyuvm.test()
class TinyTest(uvm_test):
    def build_phase(self):
        self.tc = TinyComponent("tc", self)


# Figure 4: Instantiating a component using the UVM factory
@pyuvm.test()
class TinyFactoryTest(uvm_test):
    def build_phase(self):
        self.tc = TinyComponent.create("tc", self)


# ## Creating objects with uvm_factory()
# Figure 6: Passing a component name to the factory
@pyuvm.test()
class CreateTest(uvm_test):
    def build_phase(self):
        self.tc = uvm_factory().create_component_by_name(
            "TinyComponent",
            name="tc", parent=self)


# ## Overriding types
# Figure 7: Defining an example class
class MediumComponent(uvm_component):
    async def run_phase(self):
        self.raise_objection()
        self.logger.info("I'm medium size.")
        self.drop_objection()


# Figure 8: Overriding TinyComponent with MediumComponent
@pyuvm.test()
class MediumFactoryTest(TinyFactoryTest):
    def build_phase(self):
        uvm_factory().set_type_override_by_type(
            TinyComponent, MediumComponent)
        super().build_phase()


# Figure 10: Overriding types using string names
@pyuvm.test()
class MediumNameTest(TinyFactoryTest):
    def build_phase(self):
        uvm_factory().set_type_override_by_name(
            "TinyComponent", "MediumComponent")
        super().build_phase()


# ## Factory overrides by instance
# Figure 12: Creating instances to be overridden
class TwoCompEnv(uvm_env):
    def build_phase(self):
        self.tc1 = TinyComponent.create("tc1", self)
        self.tc2 = TinyComponent.create("tc2", self)


# Figure 13: Overriding an instance by type
@pyuvm.test()
class TwoCompTest(uvm_test):
    def build_phase(self):
        uvm_factory().set_inst_override_by_type(
            TinyComponent, MediumComponent, "uvm_test_top.env.tc1")
        self.env = TwoCompEnv("env", self)


# ## Debugging the uvm_factory()
# Figure 15: Printing only overrides
@pyuvm.test()
class PrintOverrides(MediumNameTest):
    def final_phase(self):
        uvm_factory().print(0)


# Figure 17: Printing instance overrides
@pyuvm.test()
class PrintInstanceOverrides(TwoCompTest):
    def final_phase(self):
        uvm_factory().print(0)


# ### Logging uvm_factory() data
# Figure 19: Getting a string and logging the factory state
@pyuvm.test()
class LoggingOverrides(MediumNameTest):
    def final_phase(self):
        uvm_factory().debug_level = 0
        factory_log = "\n" + str(uvm_factory())
        self.logger.info(factory_log)
