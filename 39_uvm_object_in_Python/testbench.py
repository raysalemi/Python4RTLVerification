import copy
import cocotb
from pyuvm import *
# All testbenches use tinyalu_utils, so store it in a central
# place and add its path to the sys path so we can import it
import sys
from pathlib import Path
sys.path.insert(0, str(Path("..").resolve()))
from tinyalu_utils import logger  # noqa: E402


# ## Creating a string from an object
# ## Comparing objects

# Figure 2: Extending uvm_object
class PersonRecord(uvm_object):
    def __init__(self, name="", id_number=None):
        super().__init__(name)
        self.id_number = id_number

    def __str__(self):
        return f"Name: {self.get_name()}, ID: {self.id_number}"

    # Figure 6: Comparing pyuvm uvm_objects using __eq__()
    def __eq__(self, other):
        return self.id_number == other.id_number

    # Figure 15: Overriding do_copy()
    def do_copy(self, other):
        super().do_copy(other)
        self.id_number = other.id_number


# Figure 3: Printing a uvm_object
@cocotb.test()
async def test_str(_):
    xx = PersonRecord("Joe Shmoe", 37)
    print("Printing the record:", xx)
    logger.info("Logging the record: " + str(xx))


# Figure 7: Comparing uvm_objects using ==
@cocotb.test()
async def test_eq(_):
    batman = PersonRecord("Batman", 27)
    bruce_wayne = PersonRecord("Bruce Wayne", 27)
    if batman == bruce_wayne:
        logger.info("Batman is really Bruce Wayne!")
    else:
        logger.info("Who is Batman?")


# ## Copying and cloning

# Figure 8: Extending PersonRecord and leveraging __str__()
class StudentRecord(PersonRecord):
    def __init__(self, name="", id_number=None, grades=[]):
        super().__init__(name, id_number)
        self.grades = grades

    # Figure 11: Using super() to leverage the PersonRecord __str__() method
    def __str__(self):
        return super().__str__() + f" Grades: {self.grades}"

    # ### do_copy()
    # Figure 16: Using super() in do_copy to do a deep copy correctly
    def do_copy(self, other):
        super().do_copy(other)
        self.grades = list(other.grades)


# ### Copying with Python

# Figure 9: Copying an object with copy.copy()
@cocotb.test()
async def copy_copy_test(_):
    mary = StudentRecord("Mary", 33, [97, 82])
    mary_copy = StudentRecord()
    mary_copy = copy.copy(mary)
    print("mary:     ", mary)
    print("mary_copy:", mary_copy)
    print("-- grades are SAME id --")
    print("id(mary.grades):     ", id(mary.grades))
    print("id(mary_copy.grades):", id(mary_copy.grades))


# Figure 10: Making copies of all objects with copy.deepcopy()
@cocotb.test()
async def copy_deepcopy_test(_):
    mary = StudentRecord("Mary", 33, [97, 82])
    mary_copy = StudentRecord()
    mary_copy = copy.deepcopy(mary)
    print("mary:     ", mary)
    print("mary_copy:", mary_copy)
    print("-- grades are DIFFERENT id --")
    print("id(mary.grades):     ", id(mary.grades))
    print("id(mary_copy.grades):", id(mary_copy.grades))


# ## Copying with the UVM

# Figure 12: Using the copy() method in uvm_object
@cocotb.test()
async def copy_test(_):
    mary = StudentRecord("Mary", 33, [97, 82])
    mary_copy = StudentRecord()
    mary_copy.copy(mary)
    print("mary:     ", mary)
    print("mary_copy:", mary_copy)
    print("-- grades are different ids --")
    print("id(mary.grades):     ", id(mary.grades))
    print("id(mary_copy.grades):", id(mary_copy.grades))


# Figure 13: Using the clone() method in uvm_object
@cocotb.test()
async def clone_test(_):
    mary = StudentRecord("Mary", 33, [97, 82])
    mary_copy = mary.clone()
    print("mary:     ", mary)
    print("mary_copy:", mary_copy)
    print("-- grades are different ids --")
    print("id(mary.grades):     ", id(mary.grades))
    print("id(mary_copy.grades):", id(mary_copy.grades))
