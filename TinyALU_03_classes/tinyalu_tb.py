import cocotb
from tinyalu_utils import TinyAluBfm, Ops, alu_prediction
import random
import logging
import debugpy

"""
listen_host, listen_port = debugpy.listen(("localhost", 5678))
print("LISTEN_HOST:", listen_host)
print("LISTEN_PORT", listen_port)
cocotb.log.info("Waiting for Python debugger attach"
" on {}:{}".format(listen_host, listen_port))
# Suspend execution until debugger attaches
debugpy.wait_for_client()
# Break into debugger for user control
breakpoint()  # or debugpy.breakpoint() on 3.6 and below
"""

class Driver():
    def __init__(self, bfm, done):
        self.bfm = bfm
        self.done = done

    async def execute(self):
        ops = list(Ops)
        for op in ops:
            aa = random.randint(0, 255)
            bb = random.randint(0, 255)
            await self.bfm.send_op(aa, bb, op)
        await self.bfm.send_op(0, 0, 1)  # just to wait for the finish
        await self.bfm.send_op(0, 0, 1)  # just to wait for the finish
        self.done.set()


class Scoreboard():
    def __init__(self, bfm):
        self.bfm = bfm
        self.ops = []
        self.results = []
        self.cvg = set()
        self.logger = logging.getLogger()
        self.logger.setLevel(logging.DEBUG)

    async def get_cmds(self):
        while True:
            op = await self.bfm.get_cmd() 
            self.ops.append(op)
            self.cvg.add(Ops(op[2]))

    async def get_results(self):
        while True:
            result = await self.bfm.get_result()
            self.results.append(result)

    async def execute(self):
        cocotb.fork(self.get_cmds())
        cocotb.fork(self.get_results())

    def check_results(self):
        passed = True
        for cmd in self.ops:
            (aa, bb, op) = cmd
            result = self.results.pop(0)
            pr = alu_prediction(aa, bb, Ops(op), error=False)
            if result == pr:
                self.logger.info(f"PASSED: {aa} {op} {bb} = {result}")
            else:
                passed = False
                self.logger.error(
                    f"FAILED: {aa} {op} {bb} = {result} - predicted {pr}")

        if len(set(Ops) - self.cvg) > 0:
            self.logger.error(
                f"Functional coverage error. Missed: {set(Ops)-self.cvg}")
            passed = False
        else:
            self.logger.info("Covered all operations")

        return passed



@cocotb.test()
async def test_alu(dut):
    done = cocotb.triggers.Event()
    logging.basicConfig(level=logging.NOTSET)
    bfm = TinyAluBfm(dut)
    driver = Driver(bfm, done)
    scoreboard = Scoreboard(bfm)
    await bfm.reset()
    cocotb.fork(bfm.driver_bfm())
    cocotb.fork(bfm.result_mon_bfm())
    cocotb.fork(bfm.cmd_mon_bfm())
    cocotb.fork(driver.execute())
    cocotb.fork(scoreboard.execute())
    await done.wait()
    passed = scoreboard.check_results()
    assert passed
