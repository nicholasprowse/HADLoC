import sys

import utils
from text_utils import CodeObject, PositionedString

code = ['']


def print_error(*args, sep=' ', end='\n'):
    """
    Prints the given arguments in to the standard error buffer. Functions very similarly to regular print() function
    Args:
        *args: list of strings to print out
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
            print_error("{} Error: Error occurred during the handling of the exception:"
                        .format(self.ERROR_NAMES[self.EXCEPTION]))
            print_error("\t{} Error: {}".format(self.error_type, self.msg))
            print_error("{} is not a valid HADLoC Exception type".format(self.error_type))
            raise SystemExit

    def display(self):
        """Displays the error without terminating execution"""
        self.check_valid_error()
        print_error(f"{self.ERROR_NAMES[self.error_type]} Error: {self.msg}")


class CompilerException(HADLOCException):
    """
    Creates an exception used for displaying errors in code.

    Args:
        error_type (int): The type of error
        msg (str): A message advising the user what the error is
        value (PositionedString or CodeObject): The string within the code that caused the error. This must be a
            PositionedString, so that the location of the error in the original file can be identified. A CodeObject
            may also be passed in for the value argument, and the text attribute will be extracted from it.
    """
    file_name = ''

    def __init__(self, error_type, msg, value: CodeObject | PositionedString):
        self.error_type = error_type
        self.msg = msg
        self.value = value.text if isinstance(value, CodeObject) else value

    def display(self):
        """
        Displays the error. This will show the entire line where the offending character is,
        a pointer to the offending character, the file in which the error occurred, the type of the error,
        and the error message.
        """
        self.check_valid_error()
        error = self.ERROR_NAMES[self.error_type]
        print_error("{} Error in '{}', line {}"
                    .format(error, utils.get_file_name(CompilerException.file_name), self.value.line() + 1))
        print_error(code[self.value.line()].replace('\t', ' ' * 4))
        # count tabs before the character
        tabs = 0
        for i in range(min(self.value.coordinates[0].column, len(code[self.value.line()]))):
            if code[self.value.line()][i] == '\t':
                tabs += 1
        print_error(' ' * (self.value.coordinates[0].column + 3 * tabs),
                    '^' * (self.value.coordinates[-1].column - self.value.coordinates[0].column + 1), sep='')

        print_error(error, " Error: ", self.msg, sep='')
        return True


class FileError(HADLOCException):

    def __init__(self, file_name, msg):
        self.file_name = file_name
        self.error_type = self.FILE
        self.msg = msg

    def display(self):
        self.check_valid_error()
        print_error("File Error in file: '{}'".format(utils.get_file_name(self.file_name)))
        print_error(self.msg)
