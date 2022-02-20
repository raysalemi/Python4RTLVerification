import pyuvm
from pyuvm import *
import logging


# ## Creating log messages

# Figure 2: Logging messages of all levels

class LogComp(uvm_component):
    async def run_phase(self):
        self.raise_objection()
        self.logger.debug("This is debug")
        self.logger.info("This is info")
        self.logger.warning("This is warning")
        self.logger.error("This is error")
        self.logger.critical("This is critical")
        self.drop_objection()


@pyuvm.test()
class LogTest(uvm_test):
    def build_phase(self):
        self.comp = LogComp("comp", self)


# ## Logging levels

# Figure 4: Setting the logging level in
# the end_of_elaboration_phase() method

@pyuvm.test()
class DebugTest(LogTest):
    def end_of_elaboration_phase(self):
        self.set_logging_level_hier(DEBUG)


# ## Logging handlers
# ### Removing the default StreamHandler

# Figure 5: Writing log entries to a file
@pyuvm.test()
class FileTest(LogTest):
    def end_of_elaboration_phase(self):
        file_handler = logging.FileHandler("log.txt", mode="w")
        self.add_logging_handler_hier(file_handler)
        self.remove_streaming_handler_hier()


# ## Disable logging

# Figure 6: Disabling log files
@pyuvm.test()
class NoLog(LogTest):
    def end_of_elaboration_phase(self):
        self.disable_logging_hier()
