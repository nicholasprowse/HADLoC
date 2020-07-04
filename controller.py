#!/usr/bin/env python3
import sys
import os

import writer
import time
import argparse
from serial.tools import list_ports
from serial import SerialException
import serial

from assembler.assembler import assemble
from error import ConsoleException, NonTerminatingException


def execute(instruction):
    instruction = instruction.replace('\\ ', '\\s')
    tokens = instruction.split()
    if tokens[0] == 'quit':
        sys.exit(0)
    if tokens[0] == 'assemble':
        return execute_assemble(tokens[1:])
    if tokens[0] == 'write':
        return execute_write(tokens[1:])
    if tokens[0] == 'read':
        return execute_read(tokens[1:])
    if tokens[0] == 'help':
        return execite_help()


"""
def execute_read(args):
    get_serial()
    if len(args) > 4:
        raise ConsoleException("Too many arguments", "read [BYTES=256] [BASE=hex] [FILE]")

    num_bytes = 256
    file = None
    base = 'hex'
    if len(args) > 0:
        if args[0].isdecimal():
            num_bytes = int(args[0])
        else:
            raise ConsoleException("Argument 1 must be a decimal integer", 'read')

    if len(args) > 1:
        if args[1] in ['bin', 'hex', 'dec']:
            base = args[1]
        else:
            raise ConsoleException("Argument 2 must be one of 'hex', 'dec' or 'bin'", 'read')

    if len(args) > 2:
        file = open(args[2], 'w')
    data = writer.read_data(ser, num_bytes)
    writer.display(data, base)
    if file is not None:
        sys.stdout = file
        writer.display(data, base)
        sys.stdout = sys.__stdout__
        file.close()
    return True
"""


def execute_write(args):
    ser = get_serial()
    if len(args) > 1:
        raise ConsoleException("Too many arguments", 'write')

    if len(args) == 0:
        raise ConsoleException("Not enough arguments", 'write')

    writer.write_data(ser, args[0])
    return True


def execite_help():
    print("Each command consists of a name, followed by a series of arguments separated by spaces")
    print("Arguments inside square brackets are optional arguments")
    print("If an argument is not given, a default value may be used which is shown inside the square brackets")
    print("Commands:")
    print("assemble [x] [x] file")
    print("\tAssembles the given assembly code file into machine code. The file argument is the full path to the file "
          "containing assembly code. The file must contain the extension '.asm'. The two optional x arguments can be "
          "either 'c' or 'w', but they cannot both be the same. If one is 'c' then the assembly will be done 'cleanly',"
          " meaning that extra unnessecary files will not be generated. The only file created will be the raw binary "
          "file containing the machine code. If one of the arguments is 'w', then the created machine code file will be"
          " written to the connected EEPROM")
    print("translate [x] [x] file")
    print("\tTranslates the given VM file into machine code. The arguments are the same as for the 'assemble' command "
          "except that the file must be a VM file with extension '.vm'.")
    print("compiles [x] [x] file")
    print("\tCompiles the given file into machine code. The arguments are the same as for the 'assemble' command "
          "except that the file must be a [LANGUAGE] file with extension '.XXX'.")
    print("read [bytes=256] [base=hex] [file]")
    print("\tReads data from the EEPROM and displays the data. The number of bytes read is specified by the 'bytes' "
          "argument. The results can be printed out in binary, decimal or hexadecimal, "
          "which is specified by setting the 'base' argument to one of 'bin', 'dec' or 'hex' respectively. "
          "The full path of a file can be specified in the 'file' argument and the data will be written in the file in "
          "the same format as it is printed. If no file is provided, the data will not be written to a file.")
    print("write file")
    print("\tWrites data to the EEPROM. The 'file' argument is the full path of the file containing the data to write. "
          "The raw binary data of the file will be written to the EEPROM.")
    print("quit")
    print("\tQuits the program")
    print("help")
    print("\tDisplays this help message")
    return True


def get_serial():
    ports = None
    print("Type help for help selecting the serial port")
    choice = 'refresh'
    while choice == 'refresh':

        ports = list_ports.comports()
        for i in range(len(ports)):
            print(str(i + 1) + ": " + ports[i].device)

        print("Select port number from the above choices or type 'refresh' to refresh the list")
        choice = input(">> ")

        while not (choice == 'refresh') and not (choice.isdecimal() and 1 <= int(choice) <= len(ports)):
            if choice == 'quit':
                sys.exit(0)
            if choice == 'help':
                print("Plug the EEPROM Writer into a USB port and select the port it is connected to by typing the "
                      "number corresponding to the port in the list above"
                      "\nIf the correct port isn't showing, you can refresh the list by typing 'refresh'"
                      "\nThe correct port will usually be something like 'dev/usbserial-' followed by a number"
                      "\nAt any time you can type 'quit' to exit the program")
            print("Please enter a port number between 1 and", len(ports),
                  "or type 'refresh' if the required port isn't listed")
            choice = input('>> ')

    ser = serial.Serial(ports[int(choice) - 1].device, 115200)
    ser.timeout = 2
    response = ser.read_until().decode()
    if len(response) is not 0:
        print(response, end="")
    else:
        raise IOError("Could not establish connection with the port '{}'".format(ports[int(choice) - 1].device))
    return ser


def connect_serial(device_name):
    try:
        ser = serial.Serial(device_name, 115200, timeout=2)
    except SerialException:
        return None
    response = ser.read_until().decode()
    if response == 'Connection acquired\r\n':
        return ser
    else:
        return None


"""
def execute_assemble(args):
    if len(args) > 2:
        raise ConsoleException("Too many arguments", 'assemble')

    if len(args) == 0:
        raise ConsoleException("Not enough arguments", 'assemble')

    file_name = args[-1].replace('\\s', ' ').replace('\\\\', '\\')
    options = ''
    if len(args) == 2:
        options = args[0]

    clean = 'c' in options
    write = 'w' in options
    for c in options:
        if c not in 'cw':
            raise ConsoleException("Invalid Option: '{}'".format(c), 'assemble')

    files = assemble(file_name)
    if clean:
        for i in range(1, len(files)):
            os.remove(files[i])
    if write:
        writer.write_data(get_serial(), files[0])
"""

"""
def parse_compileargs(args):
    while len(args) < 2:
        args.append(None)
    clean = args[0] == 'c' or args[1] == 'c'
    write = args[0] == 'w' or args[1] == 'w'
    if args[0] not in ['c', 'w', None]:
        raise ConsoleError('Invalid first argument')

    if args[1] not in ['c', 'w', None]:
        raise ConsoleError('Invalid second argument')

    if args[0] == args[1]:
        raise ConsoleError('Invalid second argument')
    return clean, write
"""


def execute_load(args):
    ser = get_serial()
    writer.write_data(ser, args.file)


def execute_read(args):
    ser = get_serial()

    data = writer.read_data(ser, args.bytes)
    base = 'hex' if args.x else ('dec' if args.d else 'bin')
    writer.display(data, base)
    if args.file is not None:
        sys.stdout = args.file
        writer.display(data, base)
        sys.stdout = sys.__stdout__
        args.file.close()


def execute_assemble(args):
    try:
        files = assemble(args.file)
        print('Successfully Assembled')
    except NonTerminatingException as exception:
        exception.display()
        return
    if args.c:
        for i in range(1, len(files)):
            os.remove(files[i])
    if args.l:
        if args.port is not None:
            ser = connect_serial(args.port)
            if ser is None:
                print("No EEPROM writer connected to serial port: {}".format(args.port))
            else:
                writer.write_data(ser, open(files[0], 'r'))
        elif args.a:
            ser = find_serialport_auto()
            if ser is None:
                print("Unable to connect to EEPROM writer. Please ensure it is connected")
            else:
                writer.write_data(ser, open(files[0], 'r'))
        else:
            writer.write_data(get_serial(), open(files[0], 'r'))


def find_serialport_auto():
    """
    Finds the port that the EEPROM writer is connected to, and returns an open serial port connection. If no EEPROM
    writer is connected, then this returns None.

    Returns:
        An open serial port connected to the EEPROM writer, or None if no EEPROM writer is connected
    """
    # This is a list of all the ports we have already checked, and verified that the EEPROM writer is not connected
    checked = []
    finished = False

    while not finished:
        finished = True
        ports = list_ports.comports()
        for port in ports:
            if port.device in checked:
                continue
            # Extract the relevant information from the port, making sure to remove any None references
            description = port.description.lower() if port.description is not None else ""
            device = port.device.lower() if port.device is not None else ""
            product = port.product.lower() if port.product is not None else ""
            hwid = port.hwid.lower() if port.hwid is not None else ""
            # Check if usb is in any of these strings. The EEPROM writer is most likely one of these ports, since it
            # must be connected through a usb port
            if 'usb' in description + device + product + hwid:
                # get the serial port, and print it out if it was connected succesfully (i.e. is not None)
                ser = connect_serial(port.device)
                if ser is not None:
                    return ser
                checked.append(port.device)
                finished = False
                break

        if finished:
            # If the EEPROM writer wasn't found on those ports, try all the others
            for port in ports:
                if port.device not in checked:
                    ser = connect_serial(port.device)
                    if ser is not None:
                        return ser
                    checked.append(port.device)
                    finished = False
                    break

    return None


def execute_serialports(args):
    """
    If the '-a' argument is not set in args, then this function simply prints out a list of currently available
    serial ports. Otherwise, this function will attempt to automatically find the serial port with which the EEPROM
    writer is connected. If found, it will print out the port, otherwise it will inform the user that a EEPROM writer
    was not able to be found
    Args:
         args: command line arguments for this command. The only argument is the '-a' argument which is either
            True or False, indicating if the correct serial port should be automatically found
    """
    ports = list_ports.comports()
    # print out the ports if a is not set
    if not args.a:
        for port in ports:
            print(port.device)

    # Otherwise we need to find the EEPROM writer
    else:
        ser = find_serialport_auto()
        if ser is not None:
            print('Connection established to serial port: ')
            print(ser.port)
            ser.close()
        else:
            print("Unable to connect to EEPROM writer. Please ensure it is connected")
        # # This indicates which ports we have already checked
        # checked = [False] * len(ports)
        # # First we check the most likely ports. These are the ports that contain the text 'usb' in their description,
        # device, product or hwid. On Mac, this will check all usb connected ports, which should find the EEPROM writer
        # # It is unknown how other operating systems will behave
        # for i in range(len(ports)):
        #     # Extract the relevant information from the port, making sure to remove any None references
        #     port = ports[i]
        #     description = port.description.lower() if port.description is not None else ""
        #     device = port.device.lower() if port.device is not None else ""
        #     product = port.product.lower() if port.product is not None else ""
        #     hwid = port.hwid.lower() if port.hwid is not None else ""
        #     # Check is usb is in any of these strings. The EEPROM writer is most likely one of these ports, since it
        #     # must be connected through a usb port
        #     if 'usb' in description + device + product + hwid:
        #         # get the serial port, and print it out if it was connected succesfully (i.e. is not None)
        #         ser = connect_serial(port.device)
        #         if ser is not None:
        #             print('Connection established to serial port:')
        #             print(port.device)
        #             ser.close()
        #             return
        #         # Mark this port as checked
        #         checked[i] = True
        #
        # # If the EEPROM writer wasn't found on those ports, try all the others
        # for i in range(len(ports)):
        #     port = ports[i]
        #     if not checked[i]:
        #         ser = connect_serial(port.device)
        #         if ser is not None:
        #             print('Connection established to serial port:')
        #             print(port.device)
        #             ser.close()
        #             return
        #
        # # EEPROM writer was not found
        # print("Unable to connect to EEPROM writer. Please ensure it is connected")


def main():
    parser = argparse.ArgumentParser(description="Compiler and program loader for unnamed computer")
    subparsers = parser.add_subparsers(help="For more information on using each command, type\n'{} command_name -h'"
                                       .format(parser.prog), dest='command', title='Commands')

    assemble_parser = subparsers.add_parser('assemble',
                                            help='Assembles the provided assembly file and writes the assembled machine'
                                                 ' code into a binary file of the same name')
    assemble_parser.description = \
        'Assembles the given assembly file into machine code. Produces 3 files as output, raw binary file containing ' \
        'the machine code, and two text files containing the binary and hex representations of the machine code, so ' \
        'the user can read the generated machine code'
    assemble_parser.add_argument('-c', action='store_true', default=False,
                                 help='Cleans up (deletes) all intermediate files. The only file left will be the raw '
                                      'binary machine code file.')
    assemble_parser.add_argument('-l', action='store_true', default=False,
                                 help='Loads the generated machine code onto a connected EEPROM')
    port_group = assemble_parser.add_mutually_exclusive_group()
    port_group.add_argument('-a', action='store_true', default=False,
                            help="Automatically selects the serial portthe EEPROM is connected to. "
                                 "Can only be used if the '-l' is used. Note: this will not work on all systems")
    port_group.add_argument('port', nargs='?',
                            help="Name of serial port to load the assembled machine code onto. For a list of available "
                                 "serial ports, type '{} serialports'".format(parser.prog))

    assemble_parser.add_argument('file', type=argparse.FileType('r'),
                                 help="The file containing the assembly code to be assembled. "
                                      "Must have the '.asm' file extension")
    assemble_parser.set_defaults(func=execute_assemble)

    read_parser = subparsers.add_parser('read', help='Reads data from a connected EEPROM')
    read_parser.description = 'Reads data from a connected EEPROM and displays the data to the console. ' \
                              'If a file is given, then this data is also saved into the file'
    read_parser.add_argument('bytes', nargs='?', type=int, default=256, choices=range(1, 1 << 15), metavar='bytes',
                             help='Number of bytes to read from the EEPROM. Must be less than 32768. '
                                  'Defaults to 256 if not supplied')
    read_parser.add_argument('file', nargs='?', type=argparse.FileType('w'),
                             help='File to save the data read from the EEPROM')
    read_parser.set_defaults(func=execute_read)
    base_group = read_parser.add_mutually_exclusive_group()
    base_group.add_argument('-x', action='store_true', default=False, help='Displays the data read in hexadecimal')
    base_group.add_argument('-d', action='store_true', default=False, help='Displays the data read in decimal')
    base_group.add_argument('-b', action='store_true', default=False, help='Displays the data read in binary')

    load_parser = subparsers.add_parser('load', help='Loads the data in the given file onto a connected EEPROM')
    load_parser.description = "Loads the given file onto a connected EEPROM. If the '-a' option is not supplied, then" \
                              "the user will be prompted to select the serial port the EEPROM is connected to"
    load_parser.add_argument('-a', action='store_true', default=False,
                             help="Automatically selects the serial port the EEPROM is connected to. "
                                  "Note: this will not work on all systems")
    load_parser.add_argument('file', type=argparse.FileType('r'),
                             help="File containing the data to load. If the file is a text file (extension: '.txt'), "
                                  "then the ascii characters '0'and '1' are the bits loaded into the file and all other"
                                  " characters are ignored. Only the first 8 bits (1 byte) on each line are loaded, and"
                                  " if there are not 8 bits on a given line, then that line is ignored. This allow the "
                                  "user to write comments anywhere in the file, so long as the machine code is the "
                                  "first 8 '0' and '1' characters in a given line. If the file is anything other than "
                                  "a text file then the raw binary data is loaded")
    load_parser.set_defaults(func=execute_load)

    serialports_parser = subparsers.add_parser('serialports',
                                               help='Displays a list of the currently available serial ports')
    serialports_parser.description = "If no options are given, then this displays a list of the currently available " \
                                     "serial ports. If the '-a' option is supplied, then the serial ports will be " \
                                     "searched to see if one is connected to an EEPROM writer. If one is found, then " \
                                     "its name will be returned"
    serialports_parser.add_argument('-a', action='store_true', default=False,
                                    help='Attempts to find the serial port the EEPROM writer is connected to, and'
                                         'returns the name of this serial port')
    serialports_parser.set_defaults(func=execute_serialports)

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        parser.exit()
    else:
        args.func(args)


if __name__ == "__main__":
    main()
