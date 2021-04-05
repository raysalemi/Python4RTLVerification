import cocotb
from cocotb.triggers import Timer
from pyuvm import *
import random
# Mailbox example


class POBox(uvm_nonblocking_get_export):
    def try_get(self):
        if random.randint(0, 3) == 0:
            return "Congratulations", True
        else:
            return None, False


class PostOffice(uvm_component):
    def build_phase(self):
        self.po_box_export = POBox("po_box_export", self)


class CompulsiveChecker(uvm_component):
    def build_phase(self):
        self.po_box_port = uvm_nonblocking_get_port("po_box_port", self)

    async def run_phase(self):
        self.raise_objection()
        got_mail = False
        while not got_mail:
            print("checking mail and got . . .", end=" ")
            mail, got_mail = self.po_box_port.try_get()
            print(mail)
            Timer(1)
        self.drop_objection()


class Community(uvm_test):
    def build_phase(self):
        self.post_office = PostOffice("post_office", self)
        self.mail_checker = CompulsiveChecker("mail_checker", self)

    def connect_phase(self):
        self.mail_checker.po_box_port.connect(self.post_office.po_box_export)


@cocotb.test()
async def mailbox(dut):
    """The mailbox example"""
    await uvm_root().run_test("Community")


# Recycling Example


class RecycleExport(uvm_put_export):
    async def put(self, datum):
        print(f"Recycling picked up {datum}")


class SanitationDept(uvm_component):
    def build_phase(self):
        self.truck_export = RecycleExport("truck", self)


class HomeOwner(uvm_component):
    def build_phase(self):
        self.curb_port = uvm_put_port("curb", self)

    async def run_phase(self):
        self.raise_objection()
        await self.curb_port.put("trash")
        for _ in range(2):
            await self.curb_port.put("more trash")
        self.drop_objection()


class CityOfBoston(uvm_test):
    def build_phase(self):
        self.homeowner = HomeOwner("homeowner", self)
        self.trash_dept = SanitationDept("trash_dept", self)

    def connect_phase(self):
        self.homeowner.curb_port.connect(self.trash_dept.truck_export)


@cocotb.test()
async def recycling(dut):
    """The recycling example"""
    await uvm_root().run_test("CityOfBoston")


# Blocking and NonBlocking Examples

class Producer(uvm_component):
    def build_phase(self):
        self.put_port = uvm_put_port("put_port", self)

    async def run_phase(self):
        for sec in range(3, -1, -1):
            await Timer(1)
            await self.put_port.put(sec)


class BlockingConsumer(uvm_component):
    def build_phase(self):
        self.get_port = uvm_get_port("get_port", self)

    async def run_phase(self):
        self.raise_objection()
        sec = None
        while sec != 0:
            sec = await self.get_port.get()
            print(sec, end=" ")
        print("Happy New Year!")
        self.drop_objection()


class NonBlockingConsumer(uvm_component):
    def build_phase(self):
        self.get_port = uvm_get_port("get_port", self)

    async def run_phase(self):
        self.raise_objection()
        sec = None
        while sec != 0:
            success = False
            while not success:
                success, sec = self.get_port.try_get()
                await Timer(1)
            print(sec, end=" ")
        print("Happy New Year!")
        self.drop_objection()


class CountdownTest(uvm_test):

    def build_phase(self):
        self.fifo = uvm_tlm_fifo("fifo", self)
        self.pro = Producer("pro", self)

    def connect_phase(self):
        self.pro.put_port.connect(self.fifo.put_export)
        self.con.get_port.connect(self.fifo.get_export)


class BlockingCountdownTest(CountdownTest):
    def build_phase(self):
        super().build_phase()
        self.con = BlockingConsumer("con", self)


@cocotb.test()
async def blocking_test(dut):
    """Demonstrate blocking Functionality"""
    await uvm_root().run_test("BlockingCountdownTest")
    assert True


class NonBlockingCountdownTest(CountdownTest):
    def build_phase(self):
        super().build_phase()
        self.con = NonBlockingConsumer("con", self)


@cocotb.test()
async def non_blocking_test(dut):
    """Demonstrate non-blocking Functionality"""
    await uvm_root().run_test("NonBlockingCountdownTest")
    assert True


# Error checking example

class my_get_export(uvm_get_export):  # oops a get export
    async def put(self, datum):
        print(f"{self.get_name()} got {datum}!", end=" ")


class port_test(uvm_test):
    def build_phase(self):
        self.pp = uvm_put_port("pp", self)
        self.e_ex = my_get_export("e_ex", self)

    def connect_phase(self):
        self.pp.connect(self.e_ex)

    async def run_phase(self):
        self.raise_objection()
        for nn in range(3):
            await self.pp.put(nn)
        self.drop_objection()


@cocotb.test()
async def error_checking(dut):
    """Error Checking example"""
    await uvm_root().run_test("port_test")
    assert True


# Nonblocking Exports

class example_nb_get_export(uvm_get_export):  # oop a get export
    def try_get(self):
        if random.randint(0, 1) == 0:
            print("Fail", end=" ")
            return False, None
        else:
            return True, random.randint(0, 50)


class nb_get_test(uvm_test):
    def build_phase(self):
        self.nbgp = uvm_nonblocking_get_port("pp", self)
        self.nbex = example_nb_get_export("nbex", self)
    
    def connect_phase(self):
        self.nbgp.connect(self.nbex)

    async def run_phase(self):
        self.raise_objection()
        for nn in range(5):
            success = False
            while not success:
                success, numb = self.nbgp.try_get()
            print(f"\nGot {numb}")
            await Timer(1)
        self.drop_objection()


@cocotb.test()
async def non_blocking_exports(dut):
    """non_blocking exports example"""
    await uvm_root().run_test("nb_get_test")
    assert True
