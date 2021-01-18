CWD=$(shell pwd)
SIM ?= icarus
VERILOG_SOURCES =$(CWD)/hdl/verilog/tinyalu.sv
MODULE := tinyalu_cocotb
COCOTB_HDL_TIMEUNIT=1us
COCOTB_HDL_TIMEPRECISION=1us
include $(shell cocotb-config --makefiles)/Makefile.sim

#   VERILOG_SOURCES =$(CWD)/hdl/verilog/tinyalu.sv

#   VHDL_SOURCES =$(CWD)/hdl/vhdl/single_cycle_add_and_xor.vhd $(CWD)/hdl/vhdl/three_cycle_mult.vhd $(CWD)/hdl/vhdl/tinyalu.vhd
