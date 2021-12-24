import cocotb
from pyuvm import *
import logging


# ## Creating log messages
class LogComp(uvm_component):
    async def run_phase(self):
        self.raise_objection()
        self.logger.debug("This is debug")
        self.logger.info("This is info")
        self.logger.warning("This is warning")
        self.logger.error("This is error")
        self.logger.critical("This is critical")
        self.drop_objection()


class LogTest(uvm_test):
    def build_phase(self):
        self.comp = LogComp("comp", self)


@cocotb.test()
async def default_logging_levels(_):
    """Demonstrate default logging levels"""
    await uvm_root().run_test(LogTest)


# ## Logging levels

class DebugTest(LogTest):
    def end_of_elaboration_phase(self):
        self.set_logging_level_hier(DEBUG)


@cocotb.test()
async def debug_logging_level(_):
    """Demonstrate debug logging level"""
    await uvm_root().run_test(DebugTest)


# ### Changing the default logging level

@cocotb.test()
async def change_default_logging_levels(_):
    """Demonstrate default logging levels"""
    uvm_report_object.set_default_logging_level(DEBUG)
    await uvm_root().run_test("LogTest")


# ## Logging handlers
# ### Removing the default StreamHandler
class FileTest(LogTest):
    def end_of_elaboration_phase(self):
        file_handler = logging.FileHandler("log.txt", mode="w")
        self.add_logging_handler_hier(file_handler)
        self.remove_streaming_handler_hier()


@cocotb.test()
async def log_to_file(_):
    """Write log messages to file with no streaming"""
    await uvm_root().run_test(FileTest)


# ## Disable logging
class NoLog(LogTest):
    def end_of_elaboration_phase(self):
        self.disable_logging_hier()


@cocotb.test()
async def disable_logging(_):
    """Demonstrated the blessed silence of disabled logging"""
    await uvm_root().run_test("NoLog")
