# HADLoC
Command line tool containing several utilities for HADLoC.

HADLoC (Harvard Architecture Discrete Logic Computer) is an 8 bit computer I constructed, primarily out of 7400 series TTL integrated circuits. 
It contains 32KB of ROM, which is preloaded with the machine code of the program to be executed. 

![20201012_134659](https://user-images.githubusercontent.com/17104216/230822816-4e70e5be-dcf6-4b46-b4e0-54baceeddee2.jpg)

I also built a EEPROM writer to load machine code onto the ROM. The `serialports`, `load` and `read` commands are intended to interface with this circuit

![PXL_20230410_042727776~2](https://user-images.githubusercontent.com/17104216/230834171-9a54b7b8-47cb-4a84-95b5-76ed8a6ff697.jpeg)

This tool currently provides 5 commands

- `assemble`: Assembles the provided assembly file and writes the assembled machine code into a binary file of the same name
- `read`: Reads data from a connected EEPROM
- `load`: Loads the data in the given file onto a connected EEPROM
- `serialports`: Displays a list of the currently available serial ports
- `emulator`: Starts the emulator running the given binary file. In debug mode, instructions can be stepped through one by one, and register/memory contents are shown

## Installation

TODO

## Usage

Type `hadloc -h` for details on how to use the tool
