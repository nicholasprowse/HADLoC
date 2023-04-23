import sys
from enum import Enum

from hadloc import utils
from hadloc.text_utils import PositionedString

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


class ExceptionType(Enum):
    EXCEPTION = "Exception"
    SYNTAX = "Syntax"
    ARG = "Argument"
    NAME = "Name"
    FILE = "File"
    SERIAL = "Serial"
    VALUE = "Value"


class HADLOCException(Exception):
    """
    This abstract class is used for exceptions that require an error message to be displayed to the user, without
    program execution terminating. The function display is used to display the error message without terminating the
    program.
    """

    def __init__(self, error_type: ExceptionType, msg: str):
        self.error_type = error_type
        self.msg = msg

    def display(self):
        """Displays the error without terminating execution"""
        print_error(f"{self.error_type} Error: {self.msg}")


class CompilerException(HADLOCException):
    """
    Creates an exception used for displaying errors in code.

    Args:
        error_type: The type of error
        msg: A message advising the user what the error is
        value: The string within the code that caused the error. This must be a PositionedString, so that the location
            of the error in the original file can be identified. A CodeObject may also be passed in for the value
            argument, and the text attribute will be extracted from it.
    """
    file_name = ''

    def __init__(self, error_type: ExceptionType, value: PositionedString, msg: str):
        self.error_type = error_type
        self.msg = msg
        self.value = value

    def display(self):
        """
        Displays the error. This will show the entire line where the offending character is,
        a pointer to the offending character, the file in which the error occurred, the type of the error,
        and the error message.
        """
        print_error(f"{self.error_type.value} Error in '{utils.get_file_name(CompilerException.file_name)}', "
                    f"line {self.value.line() + 1}")
        print_error(code[self.value.line()].replace('\t', ' ' * 4))
        # count tabs before the character
        tabs = 0
        for i in range(min(self.value.coordinates[0].column, len(code[self.value.line()]))):
            if code[self.value.line()][i] == '\t':
                tabs += 1
        print_error(' ' * (self.value.coordinates[0].column + 3 * tabs),
                    '^' * (self.value.coordinates[-1].column - self.value.coordinates[0].column + 1), sep='')

        print_error(self.error_type.value, " Error: ", self.msg, sep='')
        return True


class FileError(HADLOCException):

    def __init__(self, file_name, msg):
        self.file_name = file_name
        self.error_type = ExceptionType.FILE
        self.msg = msg

    def display(self):
        print_error("File Error in file: '{}'".format(utils.get_file_name(self.file_name)))
        print_error(self.msg)
