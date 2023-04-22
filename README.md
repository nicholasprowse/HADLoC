# HaDLOC
Command line tool containing several utilities for HADLoC.

HADLoC (Harvard Architecture Discrete Logic Computer) is an 8-bit computer I constructed, primarily out of 7400 series TTL integrated circuits. 
It contains 32KB of ROM, which is preloaded with the machine code of the program to be executed.

<img alt="20201012_134659" src="https://user-images.githubusercontent.com/17104216/230822816-4e70e5be-dcf6-4b46-b4e0-54baceeddee2.jpg" width="800"/>

I also built a EEPROM writer to load machine code onto the ROM. The `serialports`, `load` and `read` commands are intended to interface with this circuit

<img alt="PXL_20230410_042727776~2" src="https://user-images.githubusercontent.com/17104216/230834171-9a54b7b8-47cb-4a84-95b5-76ed8a6ff697.jpeg" width="800"/>

This tool currently provides 5 commands

- `assemble`: Assembles the provided assembly file and writes the assembled machine code into a binary file of the same name
- `read`: Reads data from a connected EEPROM
- `load`: Loads the data in the given file onto a connected EEPROM
- `serialports`: Displays a list of the currently available serial ports
- `emulator`: Starts the emulator running the given binary file. In debug mode, instructions can be stepped through one by one, and register/memory contents are shown

At the moment, I have created an assembly language, with an assembler to convert it into machine language. Checkout the examples folder for examples of this. In the future I plan to create a virtual machine language, that compiles down to assembly, and also a higher level language that compiles down to the VM language. I have yet to name the high level language, but it will most likely be inspired by Kotlin. In the resources folder, you can see an example of the computer running the fib.bin file, which computes the fibonacci sequence and displays the next value each time an input is recieved

For more details about the languages and computer checkout the Specifications folder. At the moment it only contains the machine language specification, which provides a bit more detail about the computer and how to program it in raw binary machine code. I plan to create a specification for the computer architecture, which describes how it works, and I will also create specifications for the three languages I plan to create, assembly, the VM language, and the high level language.

## Installation

TODO

## Usage

Type `hadloc -h` for details on how to use the tool
