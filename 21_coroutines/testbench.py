import cocotb
from cocotb.triggers import Timer, Combine
from cocotb.queue import Queue
import logging


logging.basicConfig(level=logging.NOTSET)
logger = logging.getLogger()
logger.setLevel(logging.INFO)


@cocotb.test()
async def wait_2ns(_):
    """Waits for two ns then prints"""
    await Timer(2, units="ns")
    logger.info("I am DONE waiting!")


@cocotb.test()
async def hello_world(_):
    """Say hello!"""
    logger.info("Hello, world.")


async def counter(name, delay, count, ):
    """Counts up to the count argument after delay"""
    for ii in range(1, count + 1):
        await Timer(delay, units="ns")
        logger.info(f"{name} counts {ii}")


async def wait_for_numb(numb, delay):
    """Waits for delay ns and then returns the increment of the number"""
    await Timer(delay, units="ns")
    return numb + 1


@cocotb.test()
async def counters(_):
    """Test that forks two counters and waits for them"""
    logger.info("The Count will count to five.")
    logger.info("Mom will count to three.")
    the_count = cocotb.fork(counter("The Count", 1, 5))
    mom_warning = cocotb.fork(counter("Mom", 2, 3))
    await Combine(the_count, mom_warning)
    logger.info("All the counting is finished")


@cocotb.test()
async def inc_test(_):
    """Demonstrates fork return values"""
    logging.info("sent 1")
    inc1 = cocotb.fork(wait_for_numb(1, 1))
    nn = await inc1
    logging.info(f"returned {nn}")
    inc2 = cocotb.fork(wait_for_numb(nn, 10))
    nn = await inc2
    logging.info(f"returned {nn}")


@cocotb.test()
async def awaiting_a_fork(_):
    """Learning test to see how awaiting a fork works"""
    c1 = cocotb.fork(counter("Counter 1", 1, 3))
    cr = await c1
    logger.info(f"{cr} done counting")
    c2 = cocotb.fork(counter("Counter 2", 1, 3))
    cr = await cocotb.triggers.Join(c2)
    logger.info(f"{cr} done counting")

# Producer and Consumer


async def producer(queue, nn, delay=None):
    """Produce numbers from 1 to nn and send them"""
    for datum in range(1, nn + 1):
        if delay is not None:
            await Timer(delay, units="ns")
        logger.info(f"Producer sending {datum}")
        await queue.put(datum)
        logger.info(f"Producer sent {datum}")


async def consumer(queue):
    """Get numbers and print them to the log"""
    while True:
        logger.info("Consumer getting datum")
        datum = await queue.get()
        logger.info(f"Consumer got {datum}")


@cocotb.test()
async def producer_consumer_no_delay(_):
    """Show producer and consumer with no delay"""
    queue = Queue()
    cocotb.fork(consumer(queue))
    await producer(queue, 2)
    await Timer(1, units="ns")


@cocotb.test()
async def producer_consumer_max_size_1(_):
    """Show producer and consumer with maxsize 1"""
    queue = Queue(maxsize=1)
    cocotb.fork(consumer(queue))
    await producer(queue, 2)
    await Timer(1, units="ns")


@cocotb.test()
async def producer_consumer_sim_delay(_):
    """Show producer and consumer with simulation delay"""
    queue = Queue(maxsize=1)
    cocotb.fork(consumer(queue))
    await producer(queue, 2, 5)
    await Timer(1, units="ns")
