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
    def create_string(cls, text: str = '') -> Self:
        """
        Creates a PositionedString from a str. Automatically determines the line numbers and character positions based
        on new line characters. Line break characters are removed, as line breaks can be inferred from the coordinates
        Args:
            text: String representing some text. New line characters are used to determine line numbers of characters
        """
        lines = text.splitlines(keepends=False)
        coordinates = sum(([Coordinate(i, column) for column in range(len(line))] for i, line in enumerate(lines)),
                          start=[])
        return cls(''.join(lines), coordinates)

    @classmethod
    def empty_string(cls) -> Self:
        return PositionedString("", [])

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
        char = PositionedString.empty_string()
        if len(self.text) > 0:
            char = self.text[0]
            if '0' <= char <= '9':
                return ord(char) - ord('0')
            if 'a' <= char <= 'f':
                return ord(char) - ord('a') + 10
            if 'A' <= char <= 'F':
                return ord(char) - ord('A') + 10
        raise ValueError(f"invalid literal for int() with base 16: '{char}'")

    def __eq__(self, other: Any) -> bool:
        return str(self) == str(other)

    def __lt__(self, other) -> bool:
        return str(self) < str(other)

    def __le__(self, other) -> bool:
        return str(self) <= str(other)

    def __gt__(self, other) -> bool:
        return str(self) > str(other)

    def __ge__(self, other) -> bool:
        return str(self) >= str(other)

    def __add__(self, other) -> Self:
        assert isinstance(other, PositionedString)
        return PositionedString(self.text + other.text, self.coordinates + other.coordinates)

    def __getitem__(self, key: slice | int):
        """Returns the character located at the specified index, or the slice specified by the range"""
        if isinstance(key, slice):
            return PositionedString(self.text[key], self.coordinates[key])
        return PositionedString(self.text[key], [self.coordinates[key]])

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

    def __repr__(self):     # pragma: no cover
        return f'<{self.text}, {[(x.line, x.column) for x in self.coordinates]}>'
