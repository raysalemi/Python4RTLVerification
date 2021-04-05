import cocotb
from pyuvm import *


# Wildcards

class Greeter(uvm_component):
    def build_phase(self):
        try:
            build_child = ConfigDB().get(self, "", "CHILD")
        except UVMConfigItemNotFound:
            build_child = False

        if build_child:
            self.cc = Greeter("cc", self)

    def end_of_elaboration_phase(self):
        try:
            greeting = ConfigDB().get(self, "", "GREETING")
        except UVMConfigItemNotFound:
            greeting = "Hello"
        print(f"[{self.get_full_name()}]: {greeting}")


class TopTest(uvm_test):
    def build_phase(self):
        ConfigDB().set(self, "aa", "CHILD", True)
        ConfigDB().set(self, "aa.cc", "CHILD", True)
        ConfigDB().set(self, "bb", "CHILD", True)
        self.aa = Greeter("aa", self)
        self.bb = Greeter("bb", self)

    def end_of_elaboration_phase(self):
        print("--- ConfigDB()----", ConfigDB(), "\n", "-" * 18)

    async def run_phase(self):
        self.raise_objection()
        self.drop_objection()


@cocotb.test()
async def hierarchy(dut):
    """Demonstrate ConfigDB() Hierarchy"""
    await uvm_root().run_test("TopTest")
    assert True


# Global Wildcard


class WildcardTest(uvm_test):
    def build_phase(self):
        ConfigDB().set(self, "aa", "CHILD", True)
        ConfigDB().set(self, "aa.cc", "CHILD", True)
        ConfigDB().set(self, "bb", "CHILD", True)
        ConfigDB().set(None, "*", "GREETING", "Hola")
        self.aa = Greeter("aa", self)
        self.bb = Greeter("bb", self)

    def end_of_elaboration_phase(self):
        print("--- ConfigDB()----", ConfigDB(), "\n", "-" * 18)

    async def run_phase(self):
        self.raise_objection()
        self.drop_objection()


@cocotb.test()
async def wildcard(dut):
    """Demonstrate ConfigDB() Wildcard"""
    await uvm_root().run_test("WildcardTest")
    assert True

# Path Wildcard


class PathWildcardTest(uvm_test):
    def build_phase(self):
        ConfigDB().set(self, "aa", "CHILD", True)
        ConfigDB().set(self, "aa.cc", "CHILD", True)
        ConfigDB().set(self, "bb", "CHILD", True)
        ConfigDB().set(None, "*", "GREETING", "Hola")
        ConfigDB().set(self, "aa.*", "GREETING", "Aloha")
        ConfigDB().set(self, "aa.cc.*", "GREETING", "Shalom")
        self.aa = Greeter("aa", self)
        self.bb = Greeter("bb", self)

    def end_of_elaboration_phase(self):
        print("--- ConfigDB()----", ConfigDB(), "\n", "-" * 18)

    async def run_phase(self):
        self.raise_objection()
        self.drop_objection()


@cocotb.test()
async def path_wildcard(dut):
    """Demonstrate ConfigDB() Path Wildcard"""
    await uvm_root().run_test("PathWildcardTest")
    assert True


# Depth Wildcard


class Greeter_Hey(Greeter):
    def build_phase(self):
        ConfigDB().set(self, "cc", "GREETING", "HEY!")
        super().build_phase()


class DepthWildcardTest(uvm_test):
    def build_phase(self):
        ConfigDB().set(self, "aa", "CHILD", True)
        ConfigDB().set(self, "aa.cc", "CHILD", True)
        ConfigDB().set(self, "bb", "CHILD", True)
        ConfigDB().set(None, "*", "GREETING", "Hola")
        ConfigDB().set(self, "aa.*", "GREETING", "Aloha")
        ConfigDB().set(self, "aa.cc", "GREETING", "Shalom")
        self.aa = Greeter_Hey("aa", self)
        self.bb = Greeter("bb", self)

    def end_of_elaboration_phase(self):
        print("--- ConfigDB()----", ConfigDB(), "\n", "-" * 18)

    async def run_phase(self):
        self.raise_objection()
        self.drop_objection()


@cocotb.test()
async def depth_wildcard(dut):
    """Demonstrate Depth-first Wildcard"""
    await uvm_root().run_test("DepthWildcardTest")
    assert True


# Tracing


class TracingTest(uvm_test):
    def build_phase(self):
        ConfigDB().is_tracing = True
        ConfigDB().set(self, "aa", "CHILD", True)
        ConfigDB().set(self, "aa.cc", "CHILD", True)
        ConfigDB().set(self, "bb", "CHILD", True)
        ConfigDB().set(None, "*", "GREETING", "Hola")
        ConfigDB().set(self, "aa.*", "GREETING", "Aloha")
        ConfigDB().set(self, "aa.cc", "GREETING", "Shalom")
        self.aa = Greeter_Hey("aa", self)
        self.bb = Greeter("bb", self)

    def end_of_elaboration_phase(self):
        print("--- ConfigDB()----", ConfigDB(), "\n", "-" * 18)

    async def run_phase(self):
        self.raise_objection()
        self.drop_objection()


@cocotb.test()
async def config_tracing(dut):
    """Demonstrate Config Tracing"""
    await uvm_root().run_test("TracingTest")
    assert True


# 