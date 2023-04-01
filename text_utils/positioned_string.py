from dataclasses import dataclass
from typing import Self, Any


@dataclass
class Coordinate:
    """Basic class to hold the position of a character in source code"""
    line: int
    column: int


class PositionedString:
    """
    Represents a sequence of characters, similarly to the builtin str type. Has many of the same functions as str type.
    The difference is that, with each character is associated with a coordinate that remains attached to the character
    even as the string is manipulated. Each coordinate contains the line number and column of the character in the
    original source string. Thus, even as the string is manipulated, we can always know where each character came from.
    This is particularly useful for displaying error messages. Even if we just have one part of the string, we still
    know where it came from, so we can display the entire line in the error to give context to the error.

    Typically, PositionedString objects are created using the create_string function. This creates a PositionedString
    given a str, and automatically determines the line numbers and character positions. Alternatively, the constructor
    can be used, which requires lists of the line numbers and positions of each character

    Attributes:
        text: The raw string that this object represents
        coordinates: List of Coordinate objects of the same length as text, where each element represents the position
            in source code of the corresponding character in text
    """

    def __init__(self, text: str, coordinates: list[Coordinate]):
        """
        Creates a PositionedString, given the text, line numbers and positions of each character
        Args:
            text: The raw text of the string
            coordinates: The positions in the source code, where each character within text can be found
        """
        self.text = text
        self.coordinates = coordinates

    @classmethod
    def create_string(cls, text: str = '', line: int = 0) -> Self:
        """
        Creates a PositionedString from a str. Automatically determines the line numbers and character positions based
        on new line characters. Line break characters are removed, as line breaks can be inferred from the coordinates
        Args:
            text: String representing some text. New line characters are used to determine line numbers of characters
            line: The line number to start at. By default, this is 0
        """
        lines = text.splitlines(keepends=False)
        text = ''
        coordinates = []
        for i in range(len(lines)):
            for j in range(len(lines[i])):
                text += lines[i][j]
                coordinates.append(Coordinate(i + line, j))

        return cls(text, coordinates)

    @classmethod
    def empty_string(cls) -> Self:
        return PositionedString("", [])

    def insert(self, index: int, string: str | Self) -> Self:
        """
        Inserts a string at the given index. The string is inserted such that its first character will be at the
        location given by index. PositionedStrings, or builtin str types can be inserted.

        If a builtin str type is inserted, then the coordinates of all inserted characters will be the same. If the
        character directly before the insertion is (line, col), then the inserted characters will have coordinates
        (line, col+1)

        Args:
            index: location within the String to insert the string.
            string: The string to insert
        """
        assert -(len(self.text) + 1) <= index <= len(self.text)
        if index < 0:
            index += len(self.text) + 1
        return self[:index] + string + self[index:]

    def isspace(self) -> bool:
        """Returns True if all characters in this string are whitespace"""
        return self.text.isspace()

    def isnumeric(self) -> bool:
        """Returns true if all characters in the string are numeric"""
        return self.text.isnumeric()

    def isalpha(self) -> bool:
        """Returns true if all characters in the string are alphabetic (i.e. letters)"""
        return self.text.isalpha()

    def isalnum(self) -> bool:
        """Returns true if all characters in the string are alphanumeric (i.e. letters or numbers)"""
        return self.text.isalnum()

    def __hash__(self) -> int:
        return hash(self.text)

    def __int__(self) -> int:
        """
        Converts the first character of this string into the hex value represented by it.
        Works for all hex digits (capital and lowercase).

        Raises:
            ValueError: if the first character is not a hex character
        """
        char = self.text[0]
        if '0' <= char <= '9':
            return ord(char) - ord('0')
        if 'a' <= char <= 'f':
            return ord(char) - ord('a') + 10
        if 'A' <= char <= 'F':
            return ord(char) - ord('A') + 10
        raise ValueError("invalid literal for int() with base 16: '" + char + "'")

    def __eq__(self, other: Any) -> bool:
        if type(other) == str:
            return self.text == other
        if type(other) == PositionedString:
            return self.text == other.text
        return False

    def __ne__(self, other: Any) -> bool:
        if type(other) == str:
            return self.text != other
        if type(other) == PositionedString:
            return self.text != other.text
        return True

    def __lt__(self, other: str | Self) -> bool:
        return str(self) < str(other)

    def __gt__(self, other: str | Self) -> bool:
        return str(self) > str(other)

    def __le__(self, other: str | Self) -> bool:
        return str(self) <= str(other)

    def __ge__(self, other: str | Self) -> bool:
        return str(self) >= str(other)

    def __add__(self, other: str | Self) -> Self:
        """
        If adding a regular string, and the last coordinate in this string is (line, col), then all characters in the
        string to be added will get the coordinates (line, col + 1). Otherwise, if adding a PositionedString, it
        works as you would expect
        """
        if isinstance(other, str):
            line = self.coordinates[-1].line if len(self) > 0 else 0
            column = self.coordinates[-1].column + 1 if len(self) > 0 else 0
            other = PositionedString(other, [Coordinate(line, column)] * len(other))
        return PositionedString(self.text + other.text, self.coordinates + other.coordinates)

    def __getitem__(self, key: slice | int):
        """Returns the character located at the specified index, or the slice specified by the range"""
        if isinstance(key, slice):
            return PositionedString(self.text[key], self.coordinates[key])
        return PositionedString(self.text[key], [self.coordinates[key]])

    def __delitem__(self, key: slice | int):
        """Deletes the character located at the specified index, or the slice specified by the range"""
        list_str = list(self.text)
        del list_str[key]
        self.text = ''.join(list_str)
        del self.coordinates[key]

    def line(self, index: int = 0) -> int:
        """
        Returns the line number of the character at the given index
        If no argument is provided gives the line number of the first character
        """
        return self.coordinates[index].line

    def __len__(self) -> int:
        """Returns the number of characters in this String"""
        return len(self.text)

    def __str__(self) -> str:
        return self.text

    def __repr__(self) -> str:
        return f"'{str(self)}'"
