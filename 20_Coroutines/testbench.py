import cocotb
from cocotb.triggers import Timer, Combine
import logging


logging.basicConfig(level=logging.NOTSET)
logger = logging.getLogger()
logger.setLevel(logging.INFO)


# ## Defining coroutines

# Figure 1: Hello world as a coroutine
@cocotb.test()
async def hello_world(_):
    """Say hello!"""
    logger.info("Hello, world.")


# ## Awaiting simulation time

# Figure 5 Python waits for 2 nanoseconds
@cocotb.test()
async def wait_2ns(_):
    """Waits for two ns then prints"""
    await Timer(2, units="ns")
    logger.info("I am DONE waiting!")


# ## Starting tasks

# Figure 6: counter counts up with a delay
async def counter(name, delay, count):
    """Counts up to the count argument after delay"""
    for ii in range(1, count + 1):
        await Timer(delay, units="ns")
        logger.info(f"{name} counts {ii}")


# ### Ignoring a running task

# Figure 7: Launching a task and ignoring it
@cocotb.test()
async def do_not_wait(_):
    """Launch a counter"""
    logger.info("start counting to 3")
    cocotb.start_soon(counter("simple count", 1, 3))
    logger.info("ignored running_task")


# ### Awaiting a running task

# Figure 8: Waiting for a running task
@cocotb.test()
async def wait_for_it(_):
    """Launch a counter"""
    logger.info("start counting to 3")
    running_task = cocotb.start_soon(counter("simple count", 1, 3))
    await running_task
    logger.info("waited for running task")


# ### Running tasks in parallel

# Figure 9: Mom and The Count count in parallel
@cocotb.test()
async def counters(_):
    """Test that starts two counters and waits for them"""
    logger.info("The Count will count to five.")
    logger.info("Mom will count to three.")
    the_count = cocotb.start_soon(counter("The Count", 1, 5))
    mom_warning = cocotb.start_soon(counter("Mom", 2, 3))
    await Combine(the_count, mom_warning)
    logger.info("All the counting is finished")


# ### Returning values from tasks

# Figure 12: A coroutine that increments a number
# and returns it after a delay
async def wait_for_numb(delay, numb):
    """Waits for delay ns and then returns the increment of the number"""
    await Timer(delay, units="ns")
    return numb + 1


# Figure 13: Getting a return value by awaiting the
# returned RunningTask object
@cocotb.test()
async def inc_test(_):
    """Demonstrates start_soon() return values"""
    logging.info("sent 1")
    inc1 = cocotb.start_soon(wait_for_numb(1, 1))
    nn = await inc1
    logging.info(f"returned {nn}")
    logging.info(f"sent {nn}")
    inc2 = cocotb.start_soon(wait_for_numb(10, nn))
    nn = await inc2
    logging.info(f"returned {nn}")


# Figure 15: ### Killing a task
@cocotb.test()
async def kill_a_running_task(_):
    """Kill a running task"""
    kill_me = cocotb.start_soon(counter("Kill me", 1, 1000))
    await Timer(5, units="ns")
    kill_me.kill()
    logger.info("Killed the long-running task.")
