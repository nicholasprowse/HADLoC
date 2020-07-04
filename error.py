import sys
code = ['']


class NonTerminatingException(Exception):
    """
    This abstract class is used for exceptions that require an error message to be displayed to the user, without
    program execution terminating. The function display is used to display the error message without terminating the
    program.
    """
    def display(self):
        """Displays the error without terminating execution"""
        pass

    @staticmethod
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


class CompilerException(NonTerminatingException):
    """
    Creates an exception used for displaying errors in code.

    Args:
        error_type (str): The type of error
        msg (str): A message adviding the user what the error is
        value (PositionObject): Object that caused the error. This must be a PositionObject, so that the location of
            the error in the original file can be identified
    """
    file_name = ''

    def __init__(self, error_type, msg, value):
        self.error_type = error_type
        self.msg = msg
        self.value = value

    def display(self):
        """
        Displays the error. This will show the entire line where the offending character is,
        a pointer to the offending character, the file in which the error occured, the type of the error,
        and the error message.
        """
        print(self.value.pos)
        self.printerror(
            self.error_type, " Error in '", CompilerException.file_name, "', line ", self.value.line, sep='')
        self.printerror(code[self.value.line-1].replace('\t', ' '*4))
        # count tabs before the character
        tabs = 0
        for i in range(min(self.value.pos, len(code[self.value.line-1]))):
            if code[self.value.line-1][i] == '\t':
                tabs += 1
        self.printerror(' ' * (self.value.pos + 3*tabs), '^', sep='')
        self.printerror(self.error_type, "Error: ", self.msg, sep='')
        return True


class ConsoleException(NonTerminatingException):
    """
    Exception used to inform user that the console command they have attempted to use is invalid
    """

    usages = {'assemble': "assemble [OPTIONS] <FILE_NAME>"
                          "\n\tValid Options:"
                          "\n\t\tc: Cleans (deletes) all generated files except the raw binary file"
                          "\n\t\tw: Writes the assembled machine code to a connected EEPROM",
              'write':    "write <FILE_NAME>",
              'read':     "read [BYTES=256] [BASE=hex] [FILE_NAME]"}

    def __init__(self, msg, usage):
        self.msg = msg
        self.usage = ConsoleException.usages[usage]

    def display(self):
        self.printerror(self.msg)
        self.printerror('\tUsage: ', self.usage)
        self.printerror("Try 'help' for more information")


class FileError(NonTerminatingException):

    def __init__(self, file_name, msg):
        self.file_name = file_name
        self.msg = msg

    def display(self):
        self.printerror('Error in file:', self.file_name)
        self.printerror('FileError:', self.msg)
