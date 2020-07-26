#!/usr/bin/env python3
import sys
import os


import argparse
from serial.tools import list_ports
from serial import SerialException
import serial

import writer
from assembler.assembler import assemble
from error import HADLOCException
from utils import file_name

# TODO Serial read can raise a SerialError if the connection is lost midread. Should catch these errors


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
                raise SystemExit
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
        raise HADLOCException(HADLOCException.SERIAL,
                              f"Could not establish connection with the port '{ports[int(choice) - 1].device}'")
    return ser


INCORRECT_PORT_ERROR = 0
PORT_DOES_NOT_EXIST_ERROR = 1


def connect_serial(device_name):
    ports = list_ports.comports()
    if device_name not in [port.device for port in ports]:
        return PORT_DOES_NOT_EXIST_ERROR

    try:
        ser = serial.Serial(device_name, 115200, timeout=2)
    except SerialException:
        return INCORRECT_PORT_ERROR

    response = ser.read_until().decode()
    if response == 'Connection acquired\r\n':
        ser.timeout = None
        return ser
    else:
        return INCORRECT_PORT_ERROR


def get_serial_from_args(args):
    """
    Gets the serial port gives an argparse args object. The args object must have the following 2 arguments
        a: Boolean value indicating if the serial port should be found automatically
        port: String containing the name of the serial port. Can be None
    If a is False and port is None, then the user is prompted to select a serial port using the get_serial() function
    Args:
        args: argparse args object with boolean value a and string value port (port can be None

    Returns:
        The serial port that has been selected

    Raises:
        HADLOCException: If the given method of selecting the serial port was unsuccessful
    """
    if args.a:
        ser = find_serialport_auto()
        if ser is None:
            raise HADLOCException(HADLOCException.SERIAL,
                                  'Unable to connect to EEPROM writer. Please ensure it is connected')
    elif args.port is not None:
        ser = connect_serial(args.port)
        if ser == INCORRECT_PORT_ERROR:
            raise HADLOCException(HADLOCException.SERIAL,
                                  "No EEPROM writer connected to serial port: '{}'. Please make sure the EEPROM "
                                  "writer is connected, and you select the correct serial port".format(args.port))
        elif ser == PORT_DOES_NOT_EXIST_ERROR:
            raise HADLOCException(HADLOCException.SERIAL,
                                  "The serial port '{}' does not exist. For a list of current "
                                  "serial ports use '{} serialports'".format(args.port, parser.prog))
    else:
        ser = get_serial()
    print("Connection established to programmer", flush=True)
    return ser


def execute_load(args):
    writer.write_data(get_serial_from_args(args), args.file)


def execute_read(args):
    data = writer.read_data(get_serial_from_args(args), args.bytes)
    base = 'hex' if args.x else ('dec' if args.d else 'bin')
    writer.display(sys.stdout, data, base)
    if args.file is not None:
        writer.display(args.file, data, base)
        args.file.close()


def execute_assemble(args):
    warnings, files = assemble(args.file)
    print("Successfully Assembled '{}' with {} warning{}".format(file_name(args.file), len(warnings),
                                                                 '' if len(warnings) == 1 else 's'), flush=True)
    for warning in warnings:
        print(warning)

    if args.c:
        for i in range(1, len(files)):
            os.remove(files[i])
    if args.l:
        writer.write_data(get_serial_from_args(args), open(files[0], 'r'))
        print("Successfully Loaded '{}' onto EEPROM".format(file_name(files[0])))


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
                # get the serial port, and print it out if it was connected succesfully (i.e. is not an integer (error))
                ser = connect_serial(port.device)
                if type(ser) is not int:
                    return ser
                checked.append(port.device)
                finished = False
                break

        if finished:
            # If the EEPROM writer wasn't found on those ports, try all the others
            for port in ports:
                if port.device not in checked:
                    ser = connect_serial(port.device)
                    if type(ser) is not int:
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
            raise HADLOCException(HADLOCException.SERIAL, 'Unable to connect to EEPROM writer. '
                                                          'Please ensure it is connected')


parser = None


def main():
    global parser
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
                                 "Can only be used if the '-l' is used. Note: this may not work on all operating "
                                 "systems")
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
    port_group = read_parser.add_mutually_exclusive_group()
    port_group.add_argument('-a', action='store_true', default=False,
                            help="Automatically selects the serial port the EEPROM is connected to. "
                                 "Can only be used if the '-l' is used. Note: this may not work on all operating "
                                 "systems")
    port_group.add_argument('--port',
                            help="Name of serial port to read from. For a list of available "
                                 "serial ports, type '{} serialports'".format(parser.prog))
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
    load_parser.description = "Loads the given file onto a connected EEPROM"
    port_group = load_parser.add_mutually_exclusive_group()
    port_group.add_argument('-a', action='store_true', default=False,
                            help="Automatically selects the serial port the EEPROM is connected to. "
                                 "Note: this may not work on all operating systems")
    port_group.add_argument('--port',
                            help="Name of serial port to load the file to. For a list of available "
                                 "serial ports, type '{} serialports'".format(parser.prog))
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
        try:
            args.func(args)
        except HADLOCException as exception:
            exception.display()


def test():
    f = open("/Users/nicholasprowse/Documents/Programming/HADLoC Programs/test/test.hdc")
    try:
        assemble(f)
    except HADLOCException as he:
        he.display()
    f.close()


if __name__ == "__main__":
    test()
