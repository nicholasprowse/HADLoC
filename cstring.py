
class Code:
    """
    The Code object is used to tokenize text. It is a string of text, and contains an integer offset. Whenever
    characters are indexed, they are indexed relative to this offset. The offset can be advanced in different ways,
    allowing a tokenizer to traverse through some text, without needing to save the position it is up to.
    The text is stored in a String object, meaning each character has line numbers and positions attached to it.
    This allows one to edit/substring the text, while still having a reference to where each character came from in the
    original text.

    No errors are thrown if characters are accessed which are out of range. Instead if one attempts to access a
    character out of range of the text, then the null character is returned.

    Args:
        text (str or PositionedString): The text of the code. If a PositionedString is passed, it will not be edited by
            default. If a primitive string is passed, then all comments will be removed

    Attrubutes:
        string (PositionedString): PositionedString containing the code to be processed
        offset (int): The index of the current character being processed. All functions requiring indices, are indexed
        relative to this offset
    """

    def __init__(self, text):
        self.offset = 0
        if type(text) == PositionedString:
            self.string = text
        else:
            self.string = PositionedString.create_string(text, keepends=False)
            # Add a new line character to the end of each line. The reason we removed the new lines above, is so that
            # all new line characters are now '\n' rather than '\r' or '\r\n'
            for i in range(len(self.string) - 1, 0, -1):
                if self.string[i].line() != self.string[i - 1].line():
                    self.string = self.string.insert(i, '\n'*(self.string[i].line() - self.string[i - 1].line()))

    def substring_length(self, length):
        """
        Returns a PositionedString, that is a substring of the given length and starting at the current offset.
        If the substring would extend past the length of the String, then all of the String after offset will be
        returned

        Args:
            length (int): length of the substring to be returned (starting at offset)

        Returns:
            PositionedString: PositionedString that is a substring of this starting starting at offset, with a given
                length
        """
        return self.string[self.offset: min(self.offset + length, len(self.string))]

    def substring_absolute(self, start=None, end=None):
        """
        Returns a PositionedString, that is a substring starting and ending at at the given offsets. The starting and
        ending values are absolute (not relative to the current offset). If either the start or end is not provided,
        it defaults to the current offset.
        Args:
            start (int): The index of the start of the substring
            end (int): The index of the end of the substring (not inclusive)
        Returns: A PositionedString that is a substring from start to end
        """
        if start is None:
            start = self.offset
        if end is None:
            end = self.offset
        return self.string[start: min(end, len(self.string))]

    def substring_relative(self, start=0, end=0):
        """
        Returns a PositionedString, that is a substring starting and ending at at the given offsets. The starting and
        ending values are relative to the current offset. If either the start or end is not provided, they default to 0
        start is inclusive, while end is exclusive

        Args:
            start (int): The index of the start of the substring
            end (int): The index of the end of the substring (not inclusive)
        Returns: A PositionedString that is a substring from start to end
        """
        return self.string[start + self.offset: min(end + self.offset, len(self.string))]

    def hasmore(self):
        """Returns True if there are more characters left to process"""
        return self.offset < len(self.string)

    def advance(self, amount=1):
        """
        Increments the offset by a given amount, and returns a substring of the String advanced past

        Args:
            amount (int): amount to advance

        Returns:
            String: Substring of the string advanced past
        """
        temp = self.substring_length(amount)
        self.offset += amount
        return temp

    def advancepast(self, match):
        """
        Advances past the first occurence of the given string. If no occurence of match exists in the string, then no
        text will be advanced past, and None will be returned

        Args:
            match (str): string to find the first occurence of
        Returns:
            If match was found, returns a PositionedString containing the text advanced past. Otherwise returns None.
        """
        for i in range(self.offset, len(self.string)):
            if self.string[i: i + len(match)] == match:
                temp = self.string[self.offset: i + len(match)]
                self.offset = i + len(match)
                return temp

        return None

    def matchany(self, matches):
        """
        If the code immediatly following the current offset matches one of the string in the matches argument, then that
        string is returned as a PositionedString, and the matching code is advanced past.
        If None of the strings match, returns None.
        Args:
            matches (list<str>): A list of strings to match
        Returns:
            The PositionedString that matched, or None is none of the strings matched
        """
        for match in matches:
            if self.match(match):
                return self.substring_relative(-len(match))
        return None

    def match(self, match):
        """
        If the code immediatly following the current offset matches the given string, it is advanced past,
        and True is returned. Otherwise, False is returned and nothing is advanced past.

        Args:
            match (str): The string to check for
        Returns:
            (bool): True if the given string is advanced past, False otherwise
        """
        sub = self.substring_length(len(match))
        if sub == match:
            self.offset += len(match)
            return True
        return False

    def matchrange(self, lower, upper):
        """
        If the character at the current offet is inbetween the lower and upper characters provided (inclusive), then
        this character is advanced past the character is returned. Otherwise, False is returned
        Args:
            lower (char): the lower end of the range to check
            upper (char: the upper end of the range to check

        Returns:
            If the current character is in the given range, then the character is returned, otherwise None is returned
        """
        if lower <= self[0] <= upper:
            self.offset += 1
            return self.string[self.offset - 1]
        return None

    def __len__(self):
        """Returns the length of the code after (and including the offset)"""
        return max(0, len(self.string) - self.offset)

    def __getitem__(self, item):
        """
        Returns the character at the given location, relative to the offset.
        If the requested item is out of range, the null character will be returned, with the position of the final
        character.
        """
        if item < len(self):
            return self.string[item + self.offset]
        else:
            last_char = self.string[-1]
            return PositionedString('\0', last_char.lines, last_char.positions)

    def stripwhitespace(self):
        """
        Removes all whitespace before and after each line
        """
        # remove whitespace at start
        for i in range(len(self.string)):
            if not self.string[i].isspace():
                del self.string[0:i]
                break

        # remove whitespace at end
        for i in range(len(self.string) - 1, -1, -1):
            if not self.string[i].isspace():
                del self.string[i + 1:len(self.string)]
                break

        for i in range(len(self.string) - 2, -1, -1):
            # find line boundary
            if self.string[i].line() != self.string[i + 1].line():
                start = i
                end = i + 1
                # find first non whitespace char before line boundary
                while start >= 0 and self.string[start].isspace():
                    start -= 1
                # find first non whitespace char after line boundary
                while end < len(self.string) and self.string[end].isspace():
                    end += 1
                del self.string[start + 1: end]

    def skip_whitespace(self):
        """Moves the offset past any whitespace at the current position"""
        while self[0].isspace():
            self.advance()

    def __str__(self):
        return str(self.string[self.offset:len(self.string)])

    def __repr__(self):
        return str(self)


class LinedCode:
    """
    Behaves exactly the same as a Code object but it respects line boundaries.
    This means that no functions will advance past line boundaries except the advanceline() function.
    This allows tokenizers to easily find line boundaries, as they must acknowledge them to continue advancing.

    Args:
        text (str or PositionedString): The text of the code. Trailing and leading whitespace on each line will be
            removed. If a primitive string is passed, then all comments will also be removed

    Attrubutes:
        lines (list<Code>): List of Code objects, where each one is a single line
        line (int): The line currently being processed
    """

    def __init__(self, text):
        if type(text) == str:
            text = PositionedString.create_string(text, keepends=False)
        self.lines = []
        self.line = 0

        # seperate out the lines
        linenumber = 0
        lastlineindex = 0
        for i in range(len(text)):
            if text[i].line() != linenumber:
                nextline = Code(text[lastlineindex: i])
                nextline.stripwhitespace()
                if not nextline.string.isspace():
                    self.lines.append(nextline)
                lastlineindex = i
                linenumber = text[i].line()
        lastline = Code(text[lastlineindex: len(text)])
        lastline.stripwhitespace()
        if not lastline.string.isspace():
            self.lines.append(lastline)

    def getoffset(self):
        """Returns the current index of the line that is currently being processed"""
        return self.current_line().offset

    def substring_absolute(self, start=None, end=None):
        """
        Returns a PositionedString, that is a substring starting and ending at at the given offsets. The starting and
        ending values are absolute within the current line (not relative to the current offset).
        If either the start or end is not provided, it defaults to the current offset. Substrings will not span
        multiple lines
        Args:
            start (int): The index of the start of the substring
            end (int): The index of the end of the substring (not inclusive)
        Returns: A PositionedString that is a substring from start to end
        """
        return self.current_line().substring_absolute(start=start, end=end)

    def substring_relative(self, start=0, end=0):
        """
        Returns a PositionedString, that is a substring starting and ending at at the given offsets. The starting and
        ending values are relative to the current offset.
        If either the start or end is not provided, they default to 0
        start is inclusive, while end is exclusive.
        Substrings will not span multiple lines
        Args:
            start (int): The index of the start of the substring
            end (int): The index of the end of the substring (not inclusive)
        Returns: A PositionedString that is a substring from start to end
        """
        return self.current_line().substring_relative(start=start, end=end)

    def advance(self, amount=1):
        """
        Increments the offset by a given amount, and returns a substring of the String advanced past. Will not advance
        over a line boundary. If there is a line boundary, all the remaining character before it will be advance over
        and returned. Use advanceline() to move past line boundaries

        Args:
            amount (int): amount to advance

        Returns:
            String: Substring of the string advanced past
        """
        return self.current_line().advance(amount)

    def advancepast(self, match):
        """
        Advances past the first occurence of the given string. If no occurence of match exists before the next line
        boundary, then no text will be advanced past, and None will be returned.

        Args:
            match (str): string to find the first occurence of
        Returns:
            If match was found, returns a String containing the text advanced past. Otherwise returns None.
        """
        return self.current_line().advancepast(match)

    def advanceline(self):
        """
        Advances onto the next line if and only if the current line is completed

        Returns:
            True if a line was advanced past, otherwise False
        """
        if self.line < len(self.lines) - 1 and not self.current_line().hasmore():
            self.line += 1
            return True
        return False

    def match(self, match):
        """
        If the code immediatly following the current offset matches the given string, it is advanced past,
        and True is returned. Otherwise, False is returned and nothing is advanced past.

        Args:
            match (str): The string to check for
        Returns:
            True if the given string is advanced past, False otherwise
        """
        return self.current_line().match(match)

    def matchany(self, matches):
        """
        If the code immediatly following the current offset matches one of the string in the matches argument, then that
        string is returned as a PositionedString, and the matching code is advanced past.
        If None of the strings match, returns None.
        Args:
            matches (list<str>): A list of strings to match
        Returns:
            The PositionedString that matched, or None is none of the strings matched
        """
        return self.current_line().matchany(matches)

    def matchrange(self, lower, upper):
        """
        If the character at the current offet is inbetween the lower and upper characters provided (inclusive), then
        this character is advanced past the character is returned. Otherwise, False is returned
        Args:
            lower (char): the lower end of the range to check
            upper (char: the upper end of the range to check

        Returns:
            If the current character is in the given range, then the character is returned, otherwise None is returned
        """
        return self.current_line().matchrange(lower, upper)

    def substring_length(self, length):
        """
        Returns a String object, that is a substring of the given length and starting at the current offset.
        If the substring would extend past a line boundary, then only the text upto the end of the line is returned

        Args:
            length (int): length of the substring to be returned (starting at offset)

        Returns:
            String: String object that is a substring of this starting starting at offset, with a given length
        """
        return self.current_line().substring_length(length)

    def hasmore(self):
        """Returns True if there are more characters left to process"""
        return self.line < len(self.lines) - 1 or self.current_line().hasmore()

    def current_line(self):
        """Returns the line that is currently being processed"""
        return self.lines[self.line]

    def __len__(self):
        """Returns the length of the code after (and including the offset)"""
        length = len(self.current_line())
        for i in range(self.line + 1, len(self.lines)):
            length += len(self.lines[i])
        return length

    def __getitem__(self, item):
        """
        Returns the character at the given location, relative to the offset.
        If the requested item is on a different line to the current line, then the null character is returned
        """
        return self.current_line()[item]

    def __str__(self):
        string = "('"
        for line in self.lines:
            string += str(line) + "', '"

        return string[0:-3] + ')'

    def __repr__(self):
        return str(self)


class CodeObject:
    """
    This class represents some portion of code that is being compiled. It can be used to represent tokens, but can also
    be used to represent multiple tokens grouped together in the parsing phase. It contains the original code this
    object is derived from, stored in a PositionedString, so its location within the original code is known. It also
    contains a value attribute, which contains some value that represents the object (this will vary depending on its
    use). For example, value could be an integer for an integer token. Many operators (such as addition) are overloaded.
    If the other argument is a CodeObject, the operation is applied to the value, and the two PositionObjects are added
    together

    Attributes:
        text (PositionedString): The text, from the code, that this object derives from
        value (any): The value of this object. Optional attribute that describes the code
    """

    def __init__(self, value, text):
        assert type(value) == str or type(value) == int or type(value) == float
        self.value = value
        self.text = text

    def __eq__(self, other):
        """
        Tests if this object is equal to the other. When checking for equality, only the value attribute is checked.

        Args:
            other: The other object to test equality

        Returns:
            True if the value attribute equals the other object, otherwise False
        """
        if type(other) == CodeObject:
            return self.value == other.value
        return self.value == other

    def __lt__(self, other):
        """
        Tests if this object is less than the other. Only the value attribute is relevant.

        Args:
            other: The other object to test equality

        Returns:
            True if the value attribute is less than the other object, otherwise False
        """
        if type(other) == CodeObject:
            return self.value < other.value
        return self.value < other

    def __gt__(self, other):
        """
        Tests if this object is greater than to the other. Only the value attribute is relevant.

        Args:
            other: The other object to test equality

        Returns:
            True if the value attribute is greater than the other object, otherwise False
        """
        if type(other) == CodeObject:
            return self.value > other.value
        return self.value > other

    def __le__(self, other):
        """
        Tests if this object is less than or equal to the other. Only the value attribute is relevant.

        Args:
            other: The other object to test equality

        Returns:
            True if the value attribute is less than the other object, otherwise False
        """
        if type(other) == CodeObject:
            return self.value <= other.value
        return self.value <= other

    def __ge__(self, other):
        """
        Tests if this object is greater than or equal to the other. Only the char attribute is relevant.

        Args:
            other: The other object to test equality

        Returns:
            True if the value attribute is greater than the other object, otherwise False
        """
        if type(other) == CodeObject:
            return self.value >= other.value
        return self.value >= other

    def __ne__(self, other):
        """
        Tests if this object is not equal to the other. Only the char attribute is relevant.

        Args:
            other: The other object to test equality

        Returns:
            True if the value attribute is not equal to the other object, otherwise False
        """
        if type(other) == CodeObject:
            return self.value != other.value
        return self.value != other

    def __iand__(self, other):
        """
        Inplace and for CodeObject. Ands together the two value properties,
        and adds together the text properties
        """
        if type(other) == CodeObject:
            self.value &= other.value
            self.text += other.text
        else:
            self.value &= other
        return self

    def __and__(self, other):
        """
        Bitwise and for CodeObject. Ands together the two value properties,
        and adds together the text properties
        """
        if type(other) == CodeObject:
            return CodeObject(self.value & other.value, self.text + other.text)
        return CodeObject(self.value & other, self.text)

    def __ior__(self, other):
        """
        Inplace or for CodeObject. Ors together the two value properties,
        and adds together the text properties
        """
        if type(other) == CodeObject:
            self.value |= other.value
            self.text += other.text
        else:
            self.value |= other
        return self

    def __or__(self, other):
        """
        Bitwise or for CodeObject. Ors together the two value properties,
        and adds together the text properties
        """
        if type(other) == CodeObject:
            return CodeObject(self.value | other.value, self.text + other.text)
        return CodeObject(self.value | other, self.text)

    def __iadd__(self, other):
        """
        Inplace addition for CodeObject. Ors together the two value properties,
        and adds together the text properties
        """
        if type(other) == CodeObject:
            self.value += other.value
            self.text += other.text
        else:
            self.value += other
        return self

    def __add__(self, other):
        """
        Addition for CodeObject. Adds together the two value properties,
        and adds together the text properties
        """
        if type(other) == CodeObject:
            return CodeObject(self.value + other.value, self.text + other.text)
        return CodeObject(self.value + other, self.text)

    def __isub__(self, other):
        """
        Inplace subtraction for CodeObject. Subtracts the two value properties,
        and adds together the text properties
        """
        if type(other) == CodeObject:
            self.value -= other.value
            self.text += other.text
        else:
            self.value -= other
        return self

    def __sub__(self, other):
        """
        Subtraction for CodeObject. Subtracts the two value properties,
        and adds together the text properties
        """
        if type(other) == CodeObject:
            return CodeObject(self.value - other.value, self.text + other.text)
        return CodeObject(self.value - other, self.text)

    def __lshift__(self, other):
        """
        Left shift operator for CodeObject. Left shifts this CodeObjects value by the value provided in the argument,
        and adds together the text properties
        """
        if type(other) == CodeObject:
            return CodeObject(self.value << other.value, self.text + other.text)
        return CodeObject(self.value << other, self.text)

    def __rshift__(self, other):
        """
        Right shift operator for CodeObject. Right shifts this CodeObjects value by the value provided in the argument,
        and adds together the text properties
        """
        if type(other) == CodeObject:
            return CodeObject(self.value >> other.value, self.text + other.text)
        return CodeObject(self.value >> other, self.text)

    def __hash__(self):
        """Hashes are done based on the value attribute"""
        return hash(self.value)

    def __invert__(self):
        """Returns the bitwise inverse of the value of this CodeObject, as a CodeObject"""
        return CodeObject(~self.value, self.text)

    def __neg__(self):
        """Returns the negative of the value of this CodeObject, as a CodeObject"""
        return CodeObject(-self.value, self.text)

    def __str__(self):
        return str(self.value)

    def __repr__(self):
        if self.value == self.text:
            return repr(self.value)
        return "(" + repr(self.value) + ", text=" + repr(self.text) + ')'

    def __len__(self):
        """Returns the length of the value attribute"""
        return len(self.value)


class PositionedString:
    """
    Represents a sequence of characters, similarly to the builtin str type. Has many of the same functions as str type.
    The difference is that, with each character, a line number and position is stored. This represents the position of
    the character within the original text, meaning that at any point, we can determine where each character originated
    from, even if we have split, sliced or changed the string.

    Typically PositionedString objects are created using the create_string function. This creates a PositionedString
    given a str, and automatically determines the line numbers and character positions. Alternatively, the constructor
    can be used, which requires lists of the line numbers and positions of each character

    Attributes:
        text (str): The raw string that this object represents
        lines (list<int>): List of integers of the same length as the text, where each element is the line number of
            the corresponding character in text
        positions (list<int>): List of integers of the same length as the text, where each element is the position
            of the corresponding character in text, within its line
    """

    def __init__(self, text, lines, positions):
        """
        Creates a PositionedString, given the text, line numbers and positions of each character
        Args:
            text (str): The raw text of the string
            lines (list<int>): The line number of each character in text
            positions (list<int>): The position of each character within each line
        """
        self.text = text
        self.lines = lines
        self.positions = positions

    @staticmethod
    def create_string(text='', line=0, keepends=True):
        """
        Creates a PositionedString from a str. Automatically determines the line numbers and character positions based
        on new line characters
        Args:
            text (str): str representing some text. At each line break the line attribute is incremented, and the pos
                attribute is reset
            line (int): The line number to start at. By default this is 0
            keepends (bool): Whether or not the new line characters at the end of each line should be kept or removed.
                Defaults to True, meaning the new line characters are kept
        """
        assert type(text) == str
        lines = text.splitlines(keepends=keepends)
        text = ''
        linenumbers = []
        positions = []
        for i in range(len(lines)):
            for j in range(len(lines[i])):
                text += lines[i][j]
                linenumbers.append(i + line)
                positions.append(j)

        return PositionedString(text, linenumbers, positions)

    def substring(self, start, end):
        """
        Returns a PositionedString object, that is a substring of the given starting and ending positions.
        If the substring would extend past the length of the string, then all of the string after offset will be
        returned (an error will not be raised)

        Args:
            start (int): the index of the start of the substring (inclusive)
            end (int): the index of the end of the substring (exclusive)

        Returns:
            PositionedString: the substring of this starting from start to end
        """
        return PositionedString(self.text[start:end], self.lines[start:end], self.positions[start:end])

    def insert(self, index, string):
        """
        Inserts a string at the given index. The string is inserted such that its first character will be at the
        location given by index. PositionedStrings, or builtin str types can be inserted.

        If a builtin str type is inserted, then a the line numbers of the inserted characters will be the same as the
        character deirectly before them, and the position numbers will be one more than the character before them.
        All characters inserted will be created with the same line and position values.

        Args:
            index (int): location within the String to insert the string
            string (str or String): The string to insert
        """
        assert index <= len(self.text)
        if type(string) == str:
            line = self.lines[index - 1] if index > 0 else 0
            position = self.positions[index - 1] if index > 0 else 0
            string = PositionedString(string, [line] * len(string), [position] * len(string))

        return self[:index] + string + self[index:]

    def isspace(self):
        """Returns True if all characters in this string are whitespace"""
        return self.text.isspace()

    def isnumeric(self):
        """Returns true if all characters in the string are numeric"""
        return self.text.isnumeric()

    def isalpha(self):
        """Returns true if all characters in the string are alphabetic (i.e. letters)"""
        return self.text.isalpha()

    def isalnum(self):
        """Returns true if all characters in the string are alphanumeric (i.e. letters or numbers)"""
        return self.text.isalnum()

    def __hash__(self):
        return hash(self.text)

    def __int__(self):
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

    def __eq__(self, other):
        if type(other) == str:
            return self.text == other
        if type(other) == PositionedString:
            return self.text == other.text
        return False

    def __lt__(self, other):
        assert type(other) == str or type(other) == PositionedString
        return str(self) < str(other)

    def __gt__(self, other):
        assert type(other) == str or type(other) == PositionedString
        return str(self) > str(other)

    def __le__(self, other):
        assert type(other) == str or type(other) == PositionedString
        return str(self) <= str(other)

    def __ge__(self, other):
        assert type(other) == str or type(other) == PositionedString
        return str(self) >= str(other)

    def __ne__(self, other):
        assert type(other) == str or type(other) == PositionedString
        return str(self) != str(other)

    def __add__(self, other):
        assert type(other) == PositionedString or type(other) == str
        if type(other) == str:
            line = self.lines[-1] if len(self) > 0 else 0
            position = self.positions[-1] if len(self) > 0 else 0
            other = PositionedString(other, [line] * len(other), [position] * len(other))
        return PositionedString(self.text + other.text, self.lines + other.lines, self.positions + other.positions)

    def __iadd__(self, other):
        """
        iadd is the operator overload for inplace addition.
        i.e. s += c
        Works for other PositionedString objects and builtin str types
        """
        return self + other

    def __getitem__(self, key):
        """Returns the character located at the specified index, or the slice specified by the range"""
        if isinstance(key, slice):
            return PositionedString(self.text[key], self.lines[key], self.positions[key])
        return PositionedString(self.text[key], [self.lines[key]], [self.positions[key]])

    def __delitem__(self, key):
        """Deletes the character located at the specified index, or the slice specified by the range"""
        if type(key) == slice:
            list_str = list(self.text)
            del list_str[key]
            self.text = ''.join(list_str)
        del self.lines[key]
        del self.positions[key]

    def line(self, index=0):
        """
        Returns the line number of the character at the given index
        If no argument is provided gives the line number of the first character
        """
        return self.lines[index]

    def __len__(self):
        """Returns the number of characters in this String"""
        return len(self.text)

    def __str__(self):
        return self.text

    def __repr__(self):
        return f"'{str(self)}'"
