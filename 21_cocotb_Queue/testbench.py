import cocotb
from cocotb.triggers import Timer
# Figure 1: Importing cocotb Queue classes
from cocotb.queue import Queue, QueueEmpty, QueueFull
import logging


logging.basicConfig(level=logging.NOTSET)
logger = logging.getLogger()
logger.setLevel(logging.INFO)


# ## Blocking communication

# Figure 2: A coroutine using a Queue to send data
async def Producer(queue, nn, delay=None):
    """Produce numbers from 1 to nn and send them"""
    for datum in range(1, nn + 1):
        if delay is not None:
            await Timer(delay, units="ns")
        await queue.put(datum)
        logger.info(f"Producer sent {datum}")


# Figure 3: A coroutine using a Queue to receive data
async def Consumer(queue):
    """Get numbers and print them to the log"""
    while True:
        datum = await queue.get()
        logger.info(f"Consumer got {datum}")


# ### An infinitely long queue

# Figure 4: An infinitely long Queue consumes no time
@cocotb.test()
async def infinite_queue(_):
    """Show an infinite queue"""
    queue = Queue()
    cocotb.start_soon(Consumer(queue))
    cocotb.start_soon(Producer(queue, 3))
    await Timer(1, units="ns")


# ### A Queue of size 1
# # Figure 5: A Queue of size 1 can block when it is full
@cocotb.test()
async def queue_max_size_1(_):
    """Show producer and consumer with maxsize 1"""
    queue = Queue(maxsize=1)
    cocotb.start_soon(Consumer(queue))
    cocotb.start_soon(Producer(queue, 3))
    await Timer(1, units="ns")


# ### Queues and simulation delay

# Figure 6: Demonstrating simulated time delays
# in Queue communication
@cocotb.test()
async def producer_consumer_sim_delay(_):
    """Show producer and consumer with simulation delay"""
    queue = Queue(maxsize=1)
    cocotb.start_soon(Consumer(queue))
    ptask = cocotb.start_soon(Producer(queue, 3, 5))
    await ptask
    await Timer(1, units="ns")


# ### Non-blocking communication

# Figure 7: Putting objects in a Queue without blocking
async def ProducerNoWait(queue, nn, delay=None):
    """Produce numbers from 1 to nn and send them"""
    for datum in range(1, nn + 1):
        if delay is not None:
            await Timer(delay, units="ns")
        while True:
            try:
                queue.put_nowait(datum)
                break
            except QueueFull:
                logger.info("Queue Full, waiting 1ns")
                await Timer(1, units="ns")
        logger.info(f"Producer sent {datum}")


# Figure 8: Getting objects from a Queue without blocking
async def ConsumerNoWait(queue):
    """Get numbers and print them to the log"""
    while True:
        while True:
            try:
                datum = queue.get_nowait()
                break
            except QueueEmpty:
                logger.info("Queue Empty, waiting 2 ns")
                await Timer(2, units="ns")
        logger.info(f"Consumer got {datum}")


# Figure 9: Running our nonblocking test
@cocotb.test()
async def producer_consumer_nowait(_):
    """Show producer and consumer waiting"""
    queue = Queue(maxsize=1)
    cocotb.start_soon(ConsumerNoWait(queue))
    await ProducerNoWait(queue, 3)
    await Timer(3, units="ns")
