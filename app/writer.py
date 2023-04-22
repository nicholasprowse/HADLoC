import math
import time

from . import utils
from .error import FileError

BOX_CHAR = {'HORIZONTAL': '\u2501', 'VERTICAL': '\u2503', 'CROSS': '\u254B', 'UPPER T': '\u2533'}


def display(out, data, base):
    if base == 'bin':
        for address in range(len(data)):
            out.write('{:08b}\n'.format(data[address]))
    else:
        line_length = 16 if base == 'hex' else 10
        address_length = 4 if base == 'hex' else 5
        byte_length = 2 if base == 'hex' else 3
        page_length = 256 if base == 'hex' else 200
        address_string = (' {:04X}' if base == 'hex' else ' {:5}') + ' ' + BOX_CHAR['VERTICAL']
        byte_string = (' {:02X}' if base == 'hex' else ' {:3}')

        header = BOX_CHAR['HORIZONTAL'] * (address_length + 2) + '{}' + \
            BOX_CHAR['HORIZONTAL'] * (line_length * (byte_length + 1) + 2) + '\n' + \
            ' ' * (address_length + 2) + BOX_CHAR['VERTICAL']

        for n in range(line_length):
            if n == line_length / 2:
                header += ' '
            header += ' ' + '_' * (byte_length - 1) + '{:1X}'.format(n)

        header += '\n' + BOX_CHAR['HORIZONTAL'] * (address_length + 2) + BOX_CHAR['CROSS'] + \
            BOX_CHAR['HORIZONTAL'] * (line_length * (byte_length + 1) + 2) + '\n'

        for address in range(0, len(data), line_length):
            if address % page_length == 0:
                out.write(header.format(BOX_CHAR['CROSS' if address > 0 else 'UPPER T']))
            out.write(address_string.format(address))
            for n in range(min(line_length, len(data) - address)):
                if n == line_length / 2:
                    out.write(" ")
                out.write(byte_string.format(data[address + n]))
            out.write('\n')


# ANSI escape codes
CLEAR_LINE = '\x1b[2K'
PREVIOUS_LINE = '\x1b[F'


def write_data(ser, file):
    try:
        data = read_data_from_txt(file)
    except FileError:
        file.close()
        file = open(file.name, 'rb')
        data = file.read()
        file.close()
    size = len(data)
    ser.write(bytes([ord('w'), (size - 1) >> 8, (size - 1) % 256]))
    start = time.time()
    for i in range(0, size, 64):
        end_block = min(i + 64, size)
        ser.write(data[i:end_block])
        ser.read_until()
        rem = (time.time() - start) * (size / end_block - 1)
        print(CLEAR_LINE + "Written {} of {} bytes ({:.1f}%)"
              .format(end_block, size, end_block * 100 / size))
        print(CLEAR_LINE + "Estimated Time Remaining: {:.1f} seconds".format(rem) + PREVIOUS_LINE, end='', flush=True)
    print("\n")
    ser.read_until().decode()


def read_data_from_txt(file):
    """
    Reads the binary data in the given text file. The file must be a text file.
    Only the characters '0' and '1' are read, everything else is ignored.
    The '0's and '1's are converted into 8-bit binary numbers and returned as a byte array.
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

    data = [0] * math.ceil(len(bits) / 8)
    for i in range(len(data)):
        for bit in range(min(8, len(bits) - 8 * i)):
            data[i] += bits[bit + 8 * i] << (7 - bit)

    return bytes(data)


def read_data(ser, num_bytes):
    ser.write(bytes([ord('r'), (num_bytes - 1) >> 8, (num_bytes - 1) % 256]))
    return list(ser.read(num_bytes))
