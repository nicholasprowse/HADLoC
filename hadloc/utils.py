import os
import pathlib

from hadloc.error import FileError
from _io import TextIOWrapper
from contextlib import contextmanager


def extension(file_name: str) -> str:
    """
    Returns the extension of the given file name. For example, extension('file.txt') would return 'txt'

    Args:
        file_name: the full name of the file

    Returns: the extension of the file
    """
    return file_name[file_name.rfind('.')+1:].lower()


def path_without_extension(file: TextIOWrapper) -> str:
    return file.name[:file.name.rfind('.')].lower()


def get_file_name(file: TextIOWrapper | str) -> str:
    """
    Returns the name of a given file. This is just the name, not including the path. The file argument can either be a
    file object or a string representing the path to the file
    Args:
        file: The file to get the name of. Either a file object or a string of the path to the file
    Returns: The name of the file
    """
    if isinstance(file, TextIOWrapper):
        file = file.name
    return file[file.rfind('/')+1:].lower()


def verify_file(file: TextIOWrapper, ext: str, ext_error: str) -> str:
    """
    Verifies that the given file name is valid, and returns a file object in read mode, along with the file name with
    the extension removed. This is useful to create new files with the same name but different extensions
    The file name is valid if its extension matches the extension provided in the 'ext' parameter and the file exists
    If either condition is not met a FileError will be raised. If the extension is incorrect, the provided message will
    be used for the error

    Args:
        file: File object containing the file
        ext: The extension that the given file must have
        ext_error: The error message to display if the provided file doesn't have the required extension

    Return: the full name of the file, with the extension removed

    Raises:
        FileError: if the extension is invalid
    """
    file_name = file.name
    file_ext = extension(file_name)
    if ext != file_ext:
        raise FileError(file_name, ext_error)
    return file_name[:-len(file_ext)-1]


@contextmanager
def local_open(file, *args, **kwargs):
    hadloc_directory = pathlib.Path(os.path.realpath(__file__)).parent.resolve()
    with open(os.path.join(hadloc_directory, file), *args, **kwargs) as f:
        yield f
