import serial.tools.list_ports
import sys
import math
import time
import os
import utils
from error import FileError


# TODO Decimal outputs need reformatting
def display(data, base):
    if base == 'bin':
        for address in range(len(data)):
            print("{:08b}".format(data[address]))
    else:
        for address in range(0, len(data), 16):
            if address % 512 == 0:
                print('\u2501' * 5 + ('\u254B' if address > 0 else '\u2533') + '\u2501' * (49 if base == 'hex' else 65) + '\n     \u2503 ', end="")
                for n in range(16):
                    if n == 8:
                        print(" ", end="")
                    print(("" if base == 'hex' else "_") + "_{:1X} ".format(n), end="")
                print('\n' + '\u2501' * 5 + '\u254B' + '\u2501' * (49 if base == 'hex' else 65))
            print("{:03X}_ \u2503 ".format(address // 16), end="")
            for n in range(min(16, len(data) - address)):
                if n == 8:
                    print(" ", end="")
                if base == 'hex':
                    print("{:02X} ".format(data[address + n]), end="")
                else:
                    print("{:03d} ".format(data[address + n]), end="")
            print()


def print_help():
    print("Each command consists of a name, followed by a series of arguments separated by spaces")
    print("Arguments inside square brackets are optional arguments")
    print("If an argument is not given, a default value will be used which is shown inside the square brackets")
    print("Commands:")
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


def write_data(ser, file):
    try:
        data = read_data_from_txt(file)
    except FileError:
        file.close()
        file = open(file.name, 'rb')
        data = file.read()
        file.close()
    ser.write(bytes([ord('w'), (len(data) - 1) >> 8, (len(data) - 1) % 256]))
    progress = 0
    print("Writing", len(data), "bytes to the EEPROM")
    start = time.time()
    for i in range(0, len(data), 64):
        ser.write(data[i:min(i + 64, len(data))])
        ser.read_until()
        if 100 >= int((i + 64) * 100 / len(data)) > progress + 10:
            progress = math.floor((i + 64) * 10 / len(data)) * 10
            rem = (time.time() - start) * len(data) / (i + 64) * (1 - (i + 64) / len(data))
            "Progress: {:3.1f}%, Estimated Time Remaining: {:4.1f}".format((i + 64) * 100 / len(data), rem)
            print(
                "Progress: {:5.1f}%, Estimated Time Remaining: {:5.1f} seconds".format((i + 64) * 100 / len(data), rem))
    print(ser.read_until().decode(), end="")


def read_data_from_txt(file):
    """
    Reads the binary data in the given text file. The file must be a text file.
    Only the characters '0' and '1' are read, everything else is ignored.
    The '0's and '1's are converted into 8 bit binary numbers and returned as a byte array.
    If the total number of binary digits is not a multiple of 8, the final byte is padded with zeroes.
    Args:
        file (File): The file to read

    Returns:
        (bytes) The binary data contained within the file. Only binary digits ('0' and '1') are read,
        and are converted into a byte array

    Raises:
        FileError if the file doesn't exist or, the given file does not have the '.txt' extension
    """
    utils.verify_file(file, 'txt', "File must have '.txt' extension")
    bits = []
    text = file.read()
    file.close()
    for c in text:
        if c == '0':
            bits.append(0)
        elif c == '1':
            bits.append(1)

    data = [0]*math.ceil(len(bits)/8)
    for i in range(len(data)):
        for bit in range(min(8, len(bits) - 8*i)):
            data[i] += bits[bit + 8*i] << (7 - bit)

    return bytes(data)


def read_data(ser, num_bytes):
    ser.write(bytes([ord('r'), (num_bytes - 1) >> 8, (num_bytes - 1) % 256]))
    return list(ser.read(num_bytes))


def main():
    os.chdir("/Users/nicholasprowse/Desktop")
    stdout = sys.stdout
    print("Type help for help selecting the serial port")
    choice = 'refresh'
    ports = serial.tools.list_ports.comports()
    while choice == 'refresh':
        for i in range(len(ports)):
            print(str(i + 1) + ": " + ports[i].device)

        print("Select the serial port number from the above choices or type 'refresh' to refresh the list")

        choice = input(">> ").lower()

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
            choice = input('>> ').lower()

        ports = serial.tools.list_ports.comports()

    ser = serial.Serial(ports[int(choice) - 1].device, 115200)
    print(ser.read_until().decode(), end="")
    command = [None]
    while not command[0] == 'quit':
        command = input('>> ').lower().split(" ")
        if command[0] == 'read':
            num_bytes = 256
            file = None
            base = 'hex'
            valid = True
            if len(command) > 1:
                if command[1].isdecimal():
                    num_bytes = int(command[1])
                else:
                    print("Argument 1 of 'read' must be a decimal integer")
                    valid = False
            if len(command) > 2:
                if command[2] == 'hex' or command[2] == 'dec' or command[2] == 'bin':
                    base = command[2]
                else:
                    print("Argument 2 of 'read' must be a 'hex', 'dec' or 'bin'")
                    valid = False
            if len(command) > 3:
                file = open(command[3], 'w')
            if len(command) > 4:
                print("'read' has a maximum of 3 arguments")
                valid = False
            if valid:
                data = read_data(ser, num_bytes)
                display(data, base)
                if file is not None:
                    sys.stdout = file
                    display(data, base)
                    sys.stdout = stdout
                    file.close()
                continue
        elif command[0] == 'write':
            if len(command) == 2:
                write_data(ser, command[1])
                continue
            print("'write' must have one argument")
        elif command[0] == 'help':
            print_help()
            continue
        if not command[0] == 'quit':
            print("Invalid command. Type help for help on the commands")

    ser.close()


if __name__ == "__main__":
    main()
