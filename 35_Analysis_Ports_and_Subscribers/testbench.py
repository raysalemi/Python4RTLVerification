import cocotb
from pyuvm import *
import random
# Mailbox example


class Follower(uvm_analysis_export):
    def write(self, msg):
        rsp = random.randint(1, 3)
        if rsp == 1:
            self.logger.info(f"{self.get_name()} retweets '{msg}'")
        elif rsp == 2:
            self.logger.info(f"{self.get_name()} likes  '{msg}'")
        elif rsp == 3:
            self.logger.info(f"{self.get_name()} replies to '{msg}'")


class Twitter(uvm_test):
    def build_phase(self):
        self.f1 = Follower("Tom", self)
        self.f2 = Follower("Maria", self)
        self.f3 = Follower("Prabhu", self)
        self.ap = uvm_analysis_port("ap", self)

    def connect_phase(self):
        self.ap.connect(self.f1)
        self.ap.connect(self.f2)
        self.ap.connect(self.f3)

    async def run_phase(self):
        self.raise_objection()
        self.ap.write("Hello!")
        self.drop_objection()


@cocotb.test()
async def twitter_followers(dut):
    """non_blocking exports example"""
    await uvm_root().run_test("Twitter")
    assert True
