import cocotb
import random
from pathlib import Path
import sys
# All testbenches use tinyalu_utils, so store it in a central
# place and add its path to the sys path so we can import it
sys.path.insert(0, str(Path("..").resolve()))
from tinyalu_utils import TinyAluBfm, Ops, alu_prediction, logger  # noqa: E402


# ## The BaseTester class
# Figure 2: Common behavior across all tests
class BaseTester():

    async def execute(self):
        self.bfm = TinyAluBfm()
        ops = list(Ops)
        for op in ops:
            aa, bb = self.get_operands()
            await self.bfm.send_op(aa, bb, op)
        # send two dummy operations to allow
        # last real operation to complete
        await self.bfm.send_op(0, 0, 1)
        await self.bfm.send_op(0, 0, 1)


# ### The RandomTester
# Figure 3: RandomTester overrides get_operands()
class RandomTester(BaseTester):
    def get_operands(self):
        return random.randint(0, 255), random.randint(0, 255)


# ### The MaxTester
# Figure 4: MaxTester overrides get_operands()
class MaxTester(BaseTester):
    def get_operands(self):
        return 0xFF, 0xFF


# ## The Scoreboard class
# ### Initialize the scoreboard
# Figure 5: Initializing the Scoreboard
class Scoreboard():
    def __init__(self):
        self.bfm = TinyAluBfm()
        self.cmds = []
        self.results = []
        self.cvg = set()

# ### Define the data gathering tasks
# Figure 6: The Scoreboard gets a command

    async def get_cmds(self):
        while True:
            cmd = await self.bfm.get_cmd()
            self.cmds.append(cmd)

# Figure 7: The Scoreboard gets a result
    async def get_results(self):
        while True:
            result = await self.bfm.get_result()
            self.results.append(result)

# ### The Scoreboard's start_tasks() function

# Figure 8: The scoreboard launches data-gathering tasks
    def start_tasks(self):
        cocotb.start_soon(self.get_cmds())
        cocotb.start_soon(self.get_results())

# ### The Scoreboard's check_results() function
# Figure 9: The check_results() phase
    def check_results(self):
        passed = True
        for cmd in self.cmds:
            aa, bb, op_int = cmd
            op = Ops(op_int)
            self.cvg.add(op)
            actual = self.results.pop(0)
            prediction = alu_prediction(aa, bb, op)
            if actual == prediction:
                logger.info(
                    f"PASSED: {aa:02x} {op.name} {bb:02x} = {actual:04x}")
            else:
                passed = False
                logger.error(
                    f"FAILED: {aa:02x} {op.name} {bb:02x} = {actual:04x}"
                    f" - predicted {prediction:04x}")

# Figure 10: The Scoreboard checks functional coverage
        if len(set(Ops) - self.cvg) > 0:
            logger.error(
                f"Functional coverage error. Missed: {set(Ops)-self.cvg}")
            passed = False
        else:
            logger.info("Covered all operations")
        return passed


# ## The execute_test() coroutine
# Figure 11: The execute_test coroutine runs the test
async def execute_test(tester_class):
    bfm = TinyAluBfm()
    scoreboard = Scoreboard()
    await bfm.reset()
    bfm.start_tasks()
    scoreboard.start_tasks()
# Figure 12: Execute the tester
    tester = tester_class()
    await tester.execute()
    passed = scoreboard.check_results()
    return passed


# ## The cocotb tests
# Figure 13: cocotb will launch the execute_test coroutine
@cocotb.test()
async def random_test(_):
    """Random operands"""
    passed = await execute_test(RandomTester)
    assert passed


@cocotb.test()
async def max_test(_):
    """Maximum operands"""
    passed = await execute_test(MaxTester)
    assert passed
