import cocotb
from cocotb.triggers import Timer
from cocotb.queue import Queue, QueueEmpty, QueueFull
import logging


logging.basicConfig(level=logging.NOTSET)
logger = logging.getLogger()
logger.setLevel(logging.INFO)


# ## Blocking communication
async def Producer(queue, nn, delay=None):
    """Produce numbers from 1 to nn and send them"""
    for datum in range(1, nn + 1):
        if delay is not None:
            await Timer(delay, units="ns")
        await queue.put(datum)
        logger.info(f"Producer sent {datum}")


async def Consumer(queue):
    """Get numbers and print them to the log"""
    while True:
        datum = await queue.get()
        logger.info(f"Consumer got {datum}")


# ### An infinitely long queue
@cocotb.test()
async def infinte_queue(_):
    """Show an infinite queue"""
    queue = Queue()
    cocotb.start_soon(Consumer(queue))
    cocotb.start_soon(Producer(queue, 3))
    await Timer(1, units="ns")


# ### A Queue of size 1
@cocotb.test()
async def queue_max_size_1(_):
    """Show producer and consumer with maxsize 1"""
    queue = Queue(maxsize=1)
    cocotb.start_soon(Consumer(queue))
    cocotb.start_soon(Producer(queue, 3))
    await Timer(1, units="ns")


# ### Queues and simulation delay
@cocotb.test()
async def producer_consumer_sim_delay(_):
    """Show producer and consumer with simulation delay"""
    queue = Queue(maxsize=1)
    cocotb.start_soon(Consumer(queue))
    ptask = cocotb.start_soon(Producer(queue, 3, 5))
    await ptask
    await Timer(1, units="ns")


# ### Non-blocking communication
async def ProducerNoWait(queue, nn, delay=None):
    """Produce numbers from 1 to nn and send them"""
    for datum in range(1, nn + 1):
        if delay is not None:
            await Timer(delay, units="ns")
        sent = False
        while not sent:
            try:
                queue.put_nowait(datum)
                sent = True
            except QueueFull:
                logger.info("Queue Full, waiting 1ns")
                await Timer(1, units="ns")
        logger.info(f"Producer sent {datum}")


async def ConsumerNoWait(queue):
    """Get numbers and print them to the log"""
    while True:
        got = False
        while not got:
            try:
                datum = queue.get_nowait()
                got = True
            except QueueEmpty:
                logger.info("Queue Empty, waiting 2 ns")
                await Timer(2, units="ns")
        logger.info(f"Consumer got {datum}")


@cocotb.test()
async def producer_consumer_nowait(_):
    """Show producer and consumer not waiting"""
    queue = Queue(maxsize=1)
    cocotb.start_soon(ConsumerNoWait(queue))
    await ProducerNoWait(queue, 3)
    await Timer(3, units="ns")
