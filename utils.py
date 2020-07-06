from error import FileError
from _io import TextIOWrapper


def extension(file_name):
    """
    Returns the extension of the given file name. For example, extension('file.txt') would return 'txt'

    Args:
        file_name: (str) the full name of the file

    Returns:
        (str) the extension of the file
    """
    return file_name[len(file_name) - file_name[::-1].find('.'):].lower()


def file_name(file):
    """
    Returns the name of a given file. This is just the name, not including the path. The file argument can either be a
    file object or a string representing the path to the file
    Args:
        file: The file to get the name of. Either a file object or a string of the path to the file
    Returns:
        The name of the file
    """
    if type(file) == TextIOWrapper:
        file = file.name
    return file[len(file) - file[::-1].find('/'):].lower()


def verify_file(file, ext, ext_error):
    """
    Verifies that the given file name is valid, and returns a file object in read mode, along with the file name with
    the extension removed. This is useful to create new files with the same name but different extensions
    The file name is valid if its extension matches the extesion provided in the 'ext' parameter and the file exists
    If either condition is not met a FileError will be raised. If the extension is incorrect, the provided message will
    be used for the error

    Args:
        file: (str) File object containing the file
        ext: (str) The extension that the given file must have
        ext_error: (str) The error message to display if the provided file doen't have the required extension

    Return:
        name: (TextIOWrapper, str) file is a file object of the given file, opened in read mode. name is the full
        name of the file, with the extension removed

    Raises:
        FileError if the file doesn't exist or the extension is invalid
    """
    file_name = file.name
    file_ext = extension(file_name)
    if ext != file_ext:
        raise FileError(file_name, ext_error)
    try:
        return file_name[:-len(file_ext)-1]
    except FileNotFoundError:
        raise FileError(file_name, "File not found")
