CWD=$(shell pwd)
COCOTB_REDUCED_LOG_FMT = True
SIM ?= icarus
VERILOG_SOURCES =$(CWD)/clocker.sv
MODULE := testbench
TOPLEVEL := clocker
COCOTB_HDL_TIMEUNIT=1ps
COCOTB_HDL_TIMEPRECISION=1ps
include $(shell cocotb-config --makefiles)/Makefile.sim

cleanall: clean
	@rm -rf __pycache__
	@rm -f results.xml
