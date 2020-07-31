import sys
import utils
from cstring import CodeObject

code = ['']


def printerror(*args, sep=' ', end='\n'):
    """
    Prints the given arguments in to the standard error buffer. Functions very similarly to regular print() function
    Args
        args: list of strings to print out
        sep: string to place between each arg string printed, defaults to a space, ' '
        end: string to print at end of print, defaults to a new line, '\n'
    """
    for arg in args:
        sys.stderr.buffer.write((str(arg) + sep).encode('utf-8'))
    sys.stderr.buffer.write(end.encode('utf-8'))


class HADLOCException(Exception):
    """
    This abstract class is used for exceptions that require an error message to be displayed to the user, without
    program execution terminating. The function display is used to display the error message without terminating the
    program.
    """

    # Exception types
    EXCEPTION = 0
    SYNTAX = 1
    ARG = 2
    NAME = 3
    FILE = 4
    SERIAL = 5
    VALUE = 6

    ERROR_NAMES = {EXCEPTION: "Exception", SYNTAX: "Syntax", ARG: "Argument", NAME: "Name", FILE: "File",
                   SERIAL: "Serial", VALUE: "Value"}

    def __init__(self, error_type, msg):
        self.error_type = error_type
        self.msg = msg

    def check_valid_error(self):
        """Checks if the error type is a valid exception. If not, raises an exception describing the error and quits"""
        if self.error_type not in self.ERROR_NAMES.keys():
            printerror("{} Error: Error occured during the handling of the exception:"
                       .format(self.ERROR_NAMES[self.EXCEPTION]))
            printerror("\t{} Error: {}".format(self.error_type, self.msg))
            printerror("{} is not a valid HADLoC Exception type".format(self.error_type))
            raise SystemExit

    def display(self):
        """Displays the error without terminating execution"""
        self.check_valid_error()
        printerror(f"{self.ERROR_NAMES[self.error_type]} Error: {self.msg}")


class CompilerException(HADLOCException):
    """
    Creates an exception used for displaying errors in code.

    Args:
        error_type (int): The type of error
        msg (str): A message adviding the user what the error is
        value (PositionedString or CodeObject): The string within the code that caused the error. This must be a
            PositionedString, so that the location of the error in the original file can be identified. A CodeObject
            may also be passed in for the value argument, and the text attribute will be extracted from it.
    """
    file_name = ''

    def __init__(self, error_type, msg, value):
        self.error_type = error_type
        self.msg = msg
        if type(value) == CodeObject:
            value = value.text
        self.value = value

    def display(self):
        """
        Displays the error. This will show the entire line where the offending character is,
        a pointer to the offending character, the file in which the error occured, the type of the error,
        and the error message.
        """
        self.check_valid_error()
        error = self.ERROR_NAMES[self.error_type]
        printerror("{} Error in '{}', line {}"
                   .format(error, utils.get_file_name(CompilerException.file_name), self.value.line() + 1))
        printerror(code[self.value.line()].replace('\t', ' ' * 4))
        # count tabs before the character
        tabs = 0
        for i in range(min(self.value.positions[0], len(code[self.value.line()]))):
            if code[self.value.line()][i] == '\t':
                tabs += 1
        printerror(' ' * (self.value.positions[0] + 3 * tabs),
                   '^' * (self.value.positions[-1] - self.value.positions[0] + 1), sep='')

        printerror(error, " Error: ", self.msg, sep='')
        return True


class FileError(HADLOCException):

    def __init__(self, file_name, msg):
        self.file_name = file_name
        self.error_type = self.FILE
        self.msg = msg

    def display(self):
        self.check_valid_error()
        printerror("File Error in file: '{}'".format(utils.get_file_name(self.file_name)))
        printerror(self.msg)
