# Python for UVM Verification Examples
I've tested all the code examples in *Python for UVM Verification* using either Jupyter notebooks or **cocotb** directories. The notebook and directory names match the chapter headings.
## Installing cocotb
It is best to install **cocotb** before installing pyuvm, especially on Windows.

You can find [cocotb installation instructions](https://docs.cocotb.org/en/stable/install.html) on the **cocotb.org** website.

## Jupyter Notebooks
I used Jupyter notebooks for the Python-only examples. The easiest way to use these notebooks is to install Jupyter using `pip`:
```
% pip install jupyter
% cd <this repository directory>
% jupyter notebook
```
This command will launch your web browser in the directory and present you with a directory list. Open any `.ipynb` file to see the code examples.
You can learn more about Jupyter on [jupyter.org](https://jupyter.org) or simply Google the name to see many resources.
## cocotb directories
To run the examples in directories, you need the following:
Python 3.7 or later—I recommend the free [Anaconda Individual Edition](https://www.anaconda.com/products/individual)
A Verilog simulator—**cocotb** supports all the popular simulators, including the free Verilog simulator, Icarus. The tox script tests the examples Verilog.
**pyuvm** and **cocotb**—If you use pip to install pyuvm, you'll get cocotb automatically.
Install pyuvm using pip:
```
% pip install pyuvm
```
You can test all the examples by running `tox` in the example repository:
```
% cd python4uvm_examples
% pip install pytest tox
% tox
```
Tox should test all the **cocotb** examples and return a congratulatory message.
Run the **cocotb** examples by CDing into the example directory and using `make`:
```
% cd python4uvm_examples
% cd 	20_coroutines
% make
```
# Contributing to the examples
This repository's code must match the code in the printed book *Python for UVM Verification*. So it's challenging to change the code, but I'm happy to accept pull requests that fix minor typos.

# Staying up to date
Be sure to pull from this repository periodically to stay up to date with the latest repairs and changes to **cocotb**


