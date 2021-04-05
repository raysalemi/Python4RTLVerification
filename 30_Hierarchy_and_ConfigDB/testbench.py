import cocotb
from pyuvm import *


class NameMyself(uvm_component):
    def build_phase(self):
        if self.get_name() == "aa":
            self.cc = NameMyself("cc", self)

    def end_of_elaboration_phase(self):
        print("My name:", self.get_full_name())


class NameTest(uvm_test):
    def build_phase(self):
        self.aa = NameMyself("aa", self)
        self.bb = NameMyself("bb", self)

    async def run_phase(self):
        self.raise_objection()
        print("Top's name:", self.get_full_name())
        self.drop_objection()


@cocotb.test()
async def name_myself(dut):
    """Exercise hierarchy naming"""
    await uvm_root().run_test("NameTest")
    assert True


# ConfigDB Example


class ConfigNameMyself(uvm_component):
    def build_phase(self):
        try:
            build_child = ConfigDB().get(self, "", "CHILD")
        except UVMConfigItemNotFound:
            build_child = False
        if build_child:
            self.cc = ConfigNameMyself("cc", self)

    def end_of_elaboration_phase(self):
        print("My name:", self.get_full_name())


class ConfigTest(uvm_test):
    def build_phase(self):
        ConfigDB().set(self, "aa", "CHILD", False)
        ConfigDB().set(self, "bb", "CHILD", True)
        print("--- ConfigDB()----", ConfigDB(), "\n", "-" * 18)
        self.aa = ConfigNameMyself("aa", self)
        self.bb = ConfigNameMyself("bb", self)

    async def run_phase(self):
        self.raise_objection()
        print("Top's name:", self.get_full_name())
        self.drop_objection()


@cocotb.test()
async def config_play(dut):
    """Demonstrate using the ConfigDB()"""
    await uvm_root().run_test("ConfigTest")
    assert True
