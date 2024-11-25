# Tools for LNHR DAC II
This repository contains some useful tools for the Basel Precision Instruments *Low Noise High Resolution Digital to Analog Converter II* or *LNHR DAC II*. 

## List of all tools
- **Telnet driver:** A python driver for using Telnet to control the LNHR DAC II. `telnet.py` contains the driver. `telnet_examples.ipynb` contains some examples on how to use the driver.

## Some more information about the tools
### Telnet driver `telnet.py`
This driver implements the communication to the LNHR DAC II using the Telnet protocol. The driver also takes care of all the handshaking, necessary delays to avoid race conditions and raises Errors if the connection failed or a command could not be processed. Full documentation on all available commands can be found in the *Programmers Manual* (see `Further Documentation`).

To use the Telnet driver, connect your LNHR DAC II directly to your computer or network using the device's Ethernet port. Copy the `telnet.py` into your Python project. Have a look at the examples in `telnet_examples.ipynb` to get a better idea on how to use the driver. 

The Telnet driver can not be used when using the QCoDeS framework. Use the QCoDeS driver instead.

## Further Documentation
See https://www.baspi.ch/manuals for more information.

If you have purchased an LNHR DAC II, you have received an USB stick, which includes the full documentation.