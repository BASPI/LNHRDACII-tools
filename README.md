# Tools for LNHR DAC II
This repository contains some useful tools for the Basel Precision Instruments *Low Noise High Resolution Digital to Analog Converter II* or *LNHR DAC II*. 

## List of all tools
- **Telnet driver**: A python driver for using Telnet to control the LNHR DAC II. `telnet.py` contains the driver. `telnet_examples.ipynb` contains some basic examples on how to use the driver.
- **Adaptive fast 2D-scan example**: This example `fast_2D_scan_example.ipynb` can be used as a rough guide on how to create an adaptive fast 2D-scan using the LNHR DAC II and the Telnet driver `telnet.py`.

## Some more information about the tools
### Telnet driver `telnet.py`
This driver implements the communication to the LNHR DAC II using the Telnet protocol and the Ethernet interface of the LNHR DAC II. The driver also takes care of all the handshaking, necessary delays to avoid race conditions and raises Errors if the connection failed or a command could not be processed. Full documentation on all available commands can be found in the *Programmers Manual* (see `Further Documentation`).

The Telnet driver can not be used when using the QCoDeS framework. Use the QCoDeS driver instead.

### Adaptive 2D-scan example `fast_2D_scan_example.ipynb`
Using the provided Notebook, a 2D-scan as shown in the video below can be created. The video shows the adaptive 2D-scan in live speed.



## Setup
If you want the latest version of our tools, download the files from this repository and copy it into your project folder. Older Versions are available under `Releases`.

## Further Documentation
See https://www.baspi.ch/manuals for more information.

If you have purchased an LNHR DAC II, you have received an USB stick, which includes the full documentation.

## Contributing
If you found a bug or are having a serious issue, please use the GitHub issue tracker to report it.