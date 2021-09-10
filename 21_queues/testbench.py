import cocotb
from cocotb.triggers import Timer
from cocotb.queue import Queue, QueueEmpty, QueueFull
import logging


logging.basicConfig(level=logging.NOTSET)
logger = logging.getLogger()
logger.setLevel(logging.INFO)


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


async def producer_nw(queue, nn, delay=None):
    """Produce numbers from 1 to nn and send them"""
    for datum in range(1, nn + 1):
        if delay is not None:
            await Timer(delay, units="ns")
        logger.info(f"Producer sending {datum}")
        sent = False
        while not sent:
            try:
                logger.info("PUT try")
                queue.put_nowait(datum)
                sent = True
            except QueueFull:
                logger.info("Queue Full")
                await Timer(1, units="ns")
        logger.info(f"Producer sent {datum}")


async def consumer_nw(queue):
    """Get numbers and print them to the log"""
    while True:
        logger.info("Consumer getting datum")
        got = False
        while not got:
            try:
                logger.info("GET try")
                datum = queue.get_nowait()
                got = True
            except QueueEmpty:
                logger.info("Queue Empty")
                await Timer(2, units="ns")
        logger.info(f"Consumer got {datum}")


@cocotb.test()
async def producer_consumer_no_delay(dut):
    """Show producer and consumer with no delay"""
    queue = Queue()
    cocotb.fork(consumer(queue))
    await producer(queue, 2)
    await Timer(1, units="ns")


@cocotb.test()
async def producer_consumer_max_size_1(dut):
    """Show producer and consumer with maxsize 1"""
    queue = Queue(maxsize=1)
    cocotb.fork(consumer(queue))
    await producer(queue, 2)
    await Timer(1, units="ns")


@cocotb.test()
async def producer_consumer_sim_delay(dut):
    """Show producer and consumer with simulation delay"""
    queue = Queue(maxsize=1)
    cocotb.fork(consumer(queue))
    await producer(queue, 2, 5)
    await Timer(1, units="ns")


@cocotb.test()
async def producer_consumer_nowait(dut):
    """Show producer and consumer not waiting"""
    queue = Queue(maxsize=1)
    cocotb.fork(consumer_nw(queue))
    await producer_nw(queue, 2)
    await Timer(5, units="ns")
