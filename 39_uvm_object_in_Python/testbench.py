import copy
import cocotb
from pyuvm import *
# All testbenches use tinyalu_utils, so store it in a central
# place and add its path to the sys path so we can import it
import sys
from pathlib import Path
sys.path.append(str(Path("..").resolve()))
from tinyalu_utils import logger  # noqa: E402


class UserRecord(uvm_object):
    def __init__(self, name, id_number):
        super().__init__(name)
        self.id_number = id_number

    def __str__(self):
        return f"Name: {self.get_name()}, ID: {self.id_number}"

    def __eq__(self, other):
        return self.id_number == other.id_number


@cocotb.test()
async def test_str(_):
    """Test __str__()"""
    xx = UserRecord("Joe Shmoe", 37)
    print(xx)
    logger.info(str(xx))


@cocotb.test()
async def test_eq(_):
    """Test __eq__()"""
    batman = UserRecord("Batman", 27)
    bruce_wayne = UserRecord("Bruce Wayne", 27)
    if batman == bruce_wayne:
        logger.info("Batman is really Bruce Wayne!")
    else:
        logger.info("Who is Batman?")


class ListHolder(uvm_object):
    def __init__(self, name='', list=[]):
        super().__init__(name=name)
        self.list = list

    def __str__(self):
        return f"{self.get_name()}: {self.list} "


@cocotb.test()
async def obj_test(_):
    """Show obj handles"""
    lha = ListHolder("lha", ['A', 'B'])
    lhb = lha
    logger.info(f"lha_id: {id(lha)}, lhb_id: {id(lhb)} ")
    lhb.list.append("C")  # change lhb
    logger.info(str(lha))


class ShallowListHolder(ListHolder):
    def do_copy(self, rhs):
        self.list = rhs.list


@cocotb.test()
async def shallow_test(_):
    """Show shallow copy"""
    lha = ShallowListHolder("lha", ['A', 'B'])
    lhb = ShallowListHolder(lha.get_name())
    lhb.copy(lha)
    logger.info(f"lha_id: {id(lha)}, lhb_id: {id(lhb)} ")
    lhb.list.append("C")  # change lhb
    logger.info(str(lha))


class DeepListHolder(ListHolder):
    def do_copy(self, rhs):
        self.list = list(rhs.list)


@cocotb.test()
async def deep_test(_):
    """Show deep copy"""
    lha = DeepListHolder("lha", ['A', 'B'])
    lhb = DeepListHolder(lha.get_name())
    lhb.copy(lha)
    logger.info(f"lha_id: {id(lha)}, lhb_id: {id(lhb)} ")
    lhb.list.append("C")  # change lhb
    logger.info(str(lha))


@cocotb.test()
async def deepcopy_test(_):
    """Show copy.deepcopy()"""
    lha = DeepListHolder("lha", ['A', 'B'])
    lhb = copy.deepcopy(lha)
    logger.info(f"lha_id: {id(lha)}, lhb_id: {id(lhb)} ")
    lhb.list.append("C")  # change lhb
    logger.info(str(lha))


@cocotb.test()
async def clone_test(_):
    """Show clone()"""
    lha = ListHolder("lha", ['A', 'B'])
    lhb = lha.clone()
    logger.info(f"lha_id: {id(lha)}, lhb_id: {id(lhb)} ")
    lhb.list.append("C")  # change lhb
    logger.info(str(lha))
    logger.info(str(lhb))
