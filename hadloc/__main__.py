#!/usr/bin/env python3

import sys
import os

import argparse
import textwrap
from serial.tools import list_ports
from serial import SerialException
import serial

from hadloc import writer
from hadloc.assembler import assemble
from hadloc.error import HADLOCException, ExceptionType, FileError
# from hadloc.translator import translate
from hadloc.utils import get_file_name, extension
from hadloc.emulator import display


# TODO Serial read can raise a SerialError if the connection is lost mid read. Should catch these errors


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
    if len(response) != 0:
        print(response, end="")
    else:
        raise HADLOCException(ExceptionType.SERIAL,
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


def get_serial_from_args(args, program_name):
    """
    Gets the serial port gives an argparse args object. The args object must have the following 2 arguments
        auto_port: Boolean value indicating if the serial port should be found automatically
        port: String containing the name of the serial port. Can be None
    If auto_port is False and port is None, then the user is prompted to select a serial port using the get_serial()
    function
    Args:
        args: argparse args object with boolean value a and string value port (port can be None)
        program_name: name of the program obtained from parser.prog, used for error message

    Returns:
        The serial port that has been selected

    Raises:
        HADLOCException: If the given method of selecting the serial port was unsuccessful
    """
    if args.auto_port:
        ser = find_serial_port_auto()
        if ser is None:
            raise HADLOCException(ExceptionType.SERIAL,
                                  'Unable to connect to EEPROM writer. Please ensure it is connected')
    elif args.port is not None:
        ser = connect_serial(args.port)
        if ser == INCORRECT_PORT_ERROR:
            raise HADLOCException(ExceptionType.SERIAL,
                                  "No EEPROM writer connected to serial port: '{}'. Please make sure the EEPROM "
                                  "writer is connected, and you select the correct serial port".format(args.port))
        elif ser == PORT_DOES_NOT_EXIST_ERROR:
            raise HADLOCException(ExceptionType.SERIAL,
                                  "The serial port '{}' does not exist. For a list of current "
                                  "serial ports use '{} serialports'".format(args.port, program_name))
    else:
        ser = get_serial()
    print("Connection established to programmer", flush=True)
    return ser


def execute_load(args, program_name):
    writer.write_data(get_serial_from_args(args, program_name), args.file)


def execute_read(args, program_name):
    data = writer.read_data(get_serial_from_args(args, program_name), args.bytes)
    base = 'hex' if args.x else ('dec' if args.d else 'bin')
    writer.display(sys.stdout, data, base)
    if args.file is not None:
        writer.display(args.file, data, base)
        args.file.close()


def execute_compile(args, program_name):
    file_ext = extension(args.file.name)
    if file_ext == 'hdc':
        warnings, files = assemble(args.file)
    elif file_ext == 'vm':
        print('VM compilation is not supported yet, but it is coming soon!')
        raise SystemExit
        # warnings, files = translate(args.file)
    else:
        raise FileError(args.file.name, "File must have '.hdc' or '.vm' extension")

    print(f"Successfully Compiled '{get_file_name(args.file)}' with "
          f"{len(warnings)} warning{'' if len(warnings) == 1 else 's'}", flush=True)
    for warning in warnings:
        print(f"Warning: {warning}")

    if args.clean:
        for i in range(1, len(files)):
            os.remove(files[i])
    if args.load:
        writer.write_data(get_serial_from_args(args, program_name), open(files[0], 'r'))
        print("Successfully Loaded '{}' onto EEPROM".format(get_file_name(files[0])))


def find_serial_port_auto():
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
            hardware_id = port.hwid.lower() if port.hwid is not None else ""
            # Check if usb is in any of these strings. The EEPROM writer is most likely one of these ports, since it
            # must be connected through an usb port
            if 'usb' in description + device + product + hardware_id:
                # get the serial port, and print it out if it was connected successfully
                # (i.e. is not an integer (error))
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
    writer is connected. If found, it will print out the port, otherwise it will inform the user that an EEPROM writer
    could not be found
    Args:
         args: command line arguments for this command. The only argument is the '--auto_port' argument which is either
            True or False, indicating if the correct serial port should be automatically found
    """
    ports = list_ports.comports()
    # print out the ports if auto_port is not set
    if not args.auto_port:
        for port in ports:
            print(port.device)

    # Otherwise we need to find the EEPROM writer
    else:
        ser = find_serial_port_auto()
        if ser is not None:
            print('Connection established to serial port: ')
            print(ser.port)
            ser.close()
        else:
            raise HADLOCException(ExceptionType.SERIAL, 'Unable to connect to EEPROM writer. '
                                                        'Please ensure it is connected')


class MultilineFormatter(argparse.HelpFormatter):
    def _fill_text(self, text, width, indent):
        paragraphs = text.split('|n')
        multiline_text = ''
        for paragraph in paragraphs:
            paragraph = self._whitespace_matcher.sub(' ', paragraph).strip()
            formatted_paragraph = textwrap.fill(paragraph, width, initial_indent=indent, subsequent_indent=indent)
            multiline_text = f'{multiline_text}\n{formatted_paragraph}'
        return multiline_text


def main():
    parser = argparse.ArgumentParser(description="Compiler and program loader for unnamed computer")
    program_name = parser.prog
    subparsers = parser.add_subparsers(help="For more information on using each command, type\n'{} command_name -h'"
                                       .format(parser.prog), dest='command', title='Commands')

    compile_parser = subparsers.add_parser('compile',
                                           help='Compiles the provided source code file and writes the generated '
                                                'machine  code into a binary file of the same name')
    compile_parser.description = \
        "Compiles the given source code file into machine code. The code can be VM code, or assembly, and the " \
        "relevant compiler will be chosen based on the file extension. Assembly files must have extension '.hdc', " \
        "while VM files must have extension '.vm'."
    compile_parser.add_argument('-c', '--clean', action='store_true', default=False,
                                help='Cleans up (deletes) all intermediate files. The only file left will be the raw '
                                     'binary machine code file.')
    compile_parser.add_argument('-l', '--load', action='store_true', default=False,
                                help='Loads the generated machine code onto a connected EEPROM')
    port_group = compile_parser.add_mutually_exclusive_group()
    port_group.add_argument('-a', '--auto-port', action='store_true', default=False,
                            help="Automatically selects the serial port the EEPROM is connected to. "
                                 "Can only be used if '--load' is used. Note: this may not work on all operating "
                                 "systems")
    port_group.add_argument('--port',
                            help=f"Name of serial port to load the generated machine code onto. For a list of "
                                 f"available serial ports, type '{parser.prog} serialports'")

    compile_parser.add_argument('file', type=argparse.FileType('r'),
                                help="The file containing the source code to be assembled. "
                                     "Must have '.hdc' or '.vm' file extension")
    compile_parser.set_defaults(func=lambda x: execute_compile(x, program_name))

    read_parser = subparsers.add_parser('read', help='Reads data from a connected EEPROM')
    read_parser.description = 'Reads data from a connected EEPROM and displays the data to the console. ' \
                              'If a file is given, then this data is also saved into the file'
    port_group = read_parser.add_mutually_exclusive_group()
    port_group.add_argument('-a', '--auto-port', action='store_true', default=False,
                            help="Automatically selects the serial port the EEPROM is connected to. "
                                 "Note: this may not work on all operating systems")
    port_group.add_argument('--port',
                            help="Name of serial port to read from. For a list of available "
                                 "serial ports, type '{} serialports'".format(parser.prog))
    read_parser.add_argument('--bytes', type=int, default=256, choices=range(1, 1 << 15), metavar='{1-32767}',
                             help='Number of bytes to read from the EEPROM. Must be less than 32768. '
                                  'Defaults to 256 if not supplied')
    read_parser.add_argument('--file', type=argparse.FileType('w'),
                             help='File to save the data read from the EEPROM')
    read_parser.set_defaults(func=lambda x: execute_read(x, program_name))
    base_group = read_parser.add_mutually_exclusive_group()
    base_group.add_argument('-x', action='store_true', default=False, help='Displays the data read in hexadecimal')
    base_group.add_argument('-d', action='store_true', default=False, help='Displays the data read in decimal')
    base_group.add_argument('-b', action='store_true', default=False, help='Displays the data read in binary')

    load_parser = subparsers.add_parser('load', help='Loads the data in the given file onto a connected EEPROM')
    load_parser.description = "Loads the given file onto a connected EEPROM"
    port_group = load_parser.add_mutually_exclusive_group()
    port_group.add_argument('-a', '--auto-port', action='store_true', default=False,
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
    load_parser.set_defaults(func=lambda x: execute_load(x, program_name))

    serialports_parser = subparsers.add_parser('serialports',
                                               help='Displays a list of the currently available serial ports')
    serialports_parser.description = "If no options are given, then this displays a list of the currently available " \
                                     "serial ports. If the '-a' option is supplied, then the serial ports will be " \
                                     "searched to see if one is connected to an EEPROM writer. If one is found, then " \
                                     "its name will be returned"
    serialports_parser.add_argument('-a', '--auto-port', action='store_true', default=False,
                                    help='Attempts to find the serial port the EEPROM writer is connected to, and'
                                         'returns the name of this serial port')
    serialports_parser.set_defaults(func=execute_serialports)

    emulator_parser = subparsers.add_parser('emulator',
                                            help='Starts the emulator running the given binary file. In debug mode, '
                                                 'instructions can be stepped through one by one, and register/memory '
                                                 'contents are shown',
                                            formatter_class=MultilineFormatter)
    emulator_parser.description = textwrap.dedent('''
    Starts the emulator running the given binary file. In debug mode, instructions can be stepped through one by one,
    and register/memory contents are shown''')
    emulator_parser.epilog = textwrap.dedent('''
    Using the emulator|n|n

    Controls|n
    F5 - Pause/Resume execution. Pausing is only available in debug mode|n
    F6 - Execute next instruction. Only available when paused in debug mode|n
    F12 - Reset computer. To emulate real world resetting, all that is reset is the program counter.
    A well designed program should not be dependent on a clean starting state|n
    ESC - Quits the emulator|n|n

    Input|n
    To provide input to the computer, type the input, then hit enter. Hitting enter transfers the desired input into
    the I register, and sets IF. The literal value of the input is provided as a hexadecimal value in the input box.
    If the input value is not valid, an error will be shown in the input box, and pressing enter will do nothing|n|n
    There are several ways to enter the input:|n
    - If a single character is entered, then the ASCII value of the character is used. e.g. the input 'd' results in
    the decimal value of 100|n
    - If the input consists of multiple characters, it is interpreted as a numerical input. The first character
    indicates the base, and the following characters are the numerical value. Allowed bases are b, d and x for binary,
    decimal and hexadecimal respectively. For example, the input 'x20' is hexadecimal, so has a value of 32, while
    'b11000' is binary, so has a value of 24. If a base character is not given, it is interpreted as decimal. This
    means the leading d is optional for multi digit decimal inputs, but it is important to note that is is required for
    single digit inputs, as single digits are interpreted as their ASCII value. For example, '5' has a value of 53,
    while 'd5' has a value of 5''')
    emulator_parser.add_argument('-d', '--debug', action='store_true',
                                 help='Runs in debug mode. In debug mode, each instruction can be stepped through '
                                      'one by one, and register/memory contents are shown')
    emulator_parser.add_argument('file', type=argparse.FileType('rb'),
                                 help='Binary file to execute. Must contain HADLoC machine code')
    emulator_parser.set_defaults(func=display.start)

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        parser.exit()
    else:
        try:
            args.func(args)
        except HADLOCException as exception:
            exception.display()


if __name__ == "__main__":
    main()
