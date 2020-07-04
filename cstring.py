from error import CompilerException


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
        text (str or String): The text of the code. If a String object is passed, it will not be edited by default.
            If a primitive string is passed, then all comments will be removed

    Attrubutes:
        string (String): String object containing the code to be processed
        offset (int): The index of the current character being processed. All functions requiring indices, are indexed
        relative to this offset
    """

    def __init__(self, text):
        self.offset = 0
        if type(text) == String:
            self.string = text
        else:
            self.string = String(text)
            # Add space at each line boundary, so that tokens cannot span multiple lines
            for i in range(len(self.string) - 1, 0, -1):
                if self.string[i].line != self.string[i - 1].line:
                    self.string.insert(i, ' ')
            self.removecomments()

    def substring(self, length):
        """
        Returns a String object, that is a substring of the given length and starting at the current offset.
        If the substring would extend past the length of the String, then all of the String after offset will be
        returned

        Args:
            length (int): length of the substring to be returned (starting at offset)

        Returns:
            String: String object that is a substring of this starting starting at offset, with a given length
        """
        return self.string[self.offset: min(self.offset + length, len(self.string))]

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
        temp = self.substring(amount)
        self.offset += amount
        return temp

    def advancepast(self, match):
        """
        Advances past the first occurence of the given string. If no occurence of match exists in the string, then no
        text will be advanced past, and None will be returned

        Args:
            match (str): string to find the first occurence of
        Returns:
            If match was found, returns a String containing the text advanced past. Otherwise returns None.
        """
        for i in range(self.offset, len(self.string)):
            if self.string[i: i + len(match)] == match:
                temp = self.string[self.offset: i + len(match)]
                self.offset = i + len(match)
                return temp

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
        sub = self.substring(len(match))
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
        If the requested item is out of range, the null character will be returned.
        """
        if item < len(self):
            return self.string[item + self.offset]
        else:
            return String('\0')

    def removecomments(self):
        """
        Removes all comments from the code.
        There are 2 types of comment
        End of Line Comments:
            EOL comments start with '//' and end and the end of the line.
        Traditional Comments:
            Traditional comments start with '/*' and end at the first instance of '*/'.
            Traditional comments can span over multiple lines
        """
        for i in range(len(self.string) - 2, -1, -1):
            # Remove EOL comments
            if self.string.substring(i, i + 2) == '//':
                for j in range(i + 2, len(self.string) + 1):
                    if j == len(self.string):
                        del self.string[i:j]
                        break

                    if self.string[j].line != self.string[i].line:
                        del self.string[i:j]
                        break

            # Remove Traditional comments
            if self.string.substring(i, i + 2) == '/*':
                for j in range(i + 2, len(self.string) + 1):
                    if j == len(self.string):
                        raise CompilerException('Syntax', 'Comment not closed', self.string[i])
                    if self.string.substring(j, j + 2) == '*/':
                        del self.string[i:j + 2]
                        break

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
            if self.string[i].line != self.string[i + 1].line:
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


class LinedCode(Code):
    """
    Behaves exactly the same as a Code object but it respects line boundaries.
    This means that no functions will advance past line boundaries except the advanceline() function.
    This allows tokenizers to easily find line boundaries, as they must acknowledge them to continue advancing.

    Args:
        text (str or String): The text of the code. Trailing and leading whitespace on each line will be removed.
            If a primitive string is passed, then all comments will also be removed

    Attrubutes:
        lines (list<Code>): List of Code objects, where each one is a single line
        line (int): The line currently being processed
    """

    def __init__(self, text):
        super().__init__(text)
        self.lines = []
        self.line = 0

        # seperate out the lines
        linenumber = self.string[0].line
        lastlineindex = 0
        for i in range(len(self.string)):
            if self.string[i].line != linenumber:
                nextline = Code(self.string[lastlineindex: i])
                nextline.stripwhitespace()
                if not nextline.string.isspace():
                    self.lines.append(nextline)
                lastlineindex = i
                linenumber = self.string[i].line
        lastline = Code(self.string[lastlineindex: len(self.string)])
        lastline.stripwhitespace()
        if not lastline.string.isspace():
            self.lines.append(lastline)

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
        return self.lines[self.line].advance(amount)

    def advancepast(self, match):
        """
        Advances past the first occurence of the given string. If no occurence of match exists before the next line
        boundary, then no text will be advanced past, and None will be returned.

        Args:
            match (str): string to find the first occurence of
        Returns:
            If match was found, returns a String containing the text advanced past. Otherwise returns None.
        """
        return self.lines[self.line].advancepast(match)

    def advanceline(self):
        """
        Advances onto the next line if and only if the current line is completed

        Returns:
            True if a line was advanced past, otherwise False
        """
        if self.line < len(self.lines) - 1 and not self.lines[self.line].hasmore():
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
        return self.lines[self.line].match(match)

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
        return self.lines[self.line].matchrange(lower, upper)

    def substring(self, length):
        """
        Returns a String object, that is a substring of the given length and starting at the current offset.
        If the substring would extend past a line boundary, then only the text upto the end of the line is returned

        Args:
            length (int): length of the substring to be returned (starting at offset)

        Returns:
            String: String object that is a substring of this starting starting at offset, with a given length
        """
        return self.lines[self.line].substring(length)

    def hasmore(self):
        """Returns True if there are more characters left to process"""
        return self.line < len(self.lines) - 1 or self.lines[self.line].hasmore()

    def skip_whitespace(self):
        """Moves the offset past any whitespace at the current position, without moving past line boundaries"""
        self.lines[self.line].skip_whitespace()

    def __len__(self):
        """Returns the length of the code after (and including the offset)"""
        length = len(self.lines[self.line])
        for i in range(self.line + 1, len(self.lines)):
            length += len(self.lines[i])
        return length

    def __getitem__(self, item):
        """
        Returns the character at the given location, relative to the offset.
        If the requested item is on a different line to the current line, then the null character is returned
        """
        return self.lines[self.line][item]

    def __str__(self):
        string = "('"
        for line in self.lines:
            string += str(line) + "', '"

        return string[0:-3] + ')'

    def __repr__(self):
        return str(self)


class PositionObject:
    """
    Stores an object derived from some text. Stores the line number and position from with the object was originally
    derived. This is useful so that errors can be generated showing the position of the error, even if the original
    text has been modified.

    Note: Line numbers start at one, while pos starts at 0

    Args:
        value (object): The object to store
        line (int): the line number that the object was originally derived from
        pos (int): the position on the line the object was originally derived from

    Attributes:
        value (object): The object to store
        line (int): the line number that the object was originally derived from
        pos (int): the position on the line the object was originally derived from
    """

    def __init__(self, value, line, pos):
        self.value = value
        self.pos = pos
        self.line = line

    def __eq__(self, other):
        """
        Tests if this object is equal to the other. When checking for equality, only the value attribute is checked.

        Args:
            other (obj): The other object to test equality

        Returns:
            True if the value attribute equals the other object, otherwise False
        """
        if type(other) == PositionObject:
            return self.value == other.value
        return self.value == other

    def __lt__(self, other):
        """
        Tests if this object is less than the other. Only the value attribute is relevant.

        Args:
            other (obj): The other object to test equality

        Returns:
            True if the value attribute is less than the other object, otherwise False
        """
        if type(other) == PositionObject:
            return self.value < other.value
        return self.value < other

    def __gt__(self, other):
        """
        Tests if this object is greater than to the other. Only the value attribute is relevant.

        Args:
            other (obj): The other object to test equality

        Returns:
            True if the value attribute is greater than the other object, otherwise False
        """
        if type(other) == PositionObject:
            return self.value > other.value
        return self.value > other

    def __le__(self, other):
        """
        Tests if this object is less than or equal to the other. Only the value attribute is relevant.

        Args:
            other (obj): The other object to test equality

        Returns:
            True if the value attribute is less than the other object, otherwise False
        """
        if type(other) == PositionObject:
            return self.value <= other.value
        return self.value <= other

    def __ge__(self, other):
        """
        Tests if this object is greater than or equal to the other. Only the char attribute is relevant.

        Args:
            other (obj): The other object to test equality

        Returns:
            True if the value attribute is greater than the other object, otherwise False
        """
        if type(other) == PositionObject:
            return self.value >= other.value
        return self.value >= other

    def __ne__(self, other):
        """
        Tests if this object is not equal to the other. Only the char attribute is relevant.

        Args:
            other (obj): The other object to test equality

        Returns:
            True if the value attribute is not equal to the other object, otherwise False
        """
        if type(other) == PositionObject:
            return self.value != other.value
        return self.value != other

    def __str__(self):
        return "(" + repr(self.value) + ", line=" + str(self.line) + ", pos=" + str(self.pos) + ')'

    def __repr__(self):
        return str(self.value)

    def __len__(self):
        """This is included for situations where Characters are treated as length 1 strings"""
        return 1


class String(PositionObject):
    """
    Represents a sequence of Character objects. Functions very similarly to the builtin str type, but each character has
    its line number and position of where it is from in the original file. This allows the user to manipulate the
    strings however they like, while still knowing where each character came from. Thus, error messages with the
    original text from the file can be displayed, even though the strings have been changed.

    Args:
        text (list<PositionObject> or str): List of PositionObjects, each containg a character to be contained in this
        string, or a str to be converted into a String. This argument is optional, if it is not supplied an
        empty string will be created.

    Attributes:
        chars (list<PositionObject>): List of PositionObjects, each containing a charcter in this string
    """

    def __init__(self, text=None):
        if text is None:
            text = []
        assert type(text) == str or type(text) == list
        if type(text) == str:
            self.chars = []
            text = text.splitlines()
            for i in range(len(text)):
                for j in range(len(text[i])):
                    self.chars.append(PositionObject(text[i][j], i + 1, j))
        else:
            self.chars = text

        super().__init__(None, 0 if len(self.chars) == 0 else self.chars[0].line,
                         0 if len(self.chars) == 0 else self.chars[0].pos)

    def substring(self, start, end):
        """
        Returns a String object, that is a substring of the given length and starting at the current offset.
        If the substring would extend past the length of the String, then all of the String after offset will be
        returned

        Args:
            start (int): the index of the start of the substring (inclusive)
            end (int): the index of the end of the substring (exclusive)

        Returns:
            String: String object that is a substring of this starting from start to end
        """
        return String(self.chars[start: end])

    def insert(self, index, string):
        """
        Inserts a string at the given index. The string is inserted such that its first character will be at the
        location given by index. String objects, or primitive strings can be inserted.

        If a primitive string is inserted, then a the line numbers of the inserted characters will be the same as the
        character before them, andthe position numbers will be one more than the character before them. All characters
        inserted will be created with the same line and position values.

        Args:
            index (int): location within the String to insert the string
            string (str or String): The string to insert
        """
        if type(string) == str:
            for i in range(len(string) - 1, -1, -1):
                if index == 0:
                    char = PositionObject(string[i], 0, 0)
                else:
                    char = PositionObject(string[i], self.chars[index - 1].line, self.chars[index - 1].pos + 1)
                self.chars.insert(index, char)
        else:
            for i in range(len(string) - 1, -1, -1):
                self.chars.insert(index, string[i])

    def isspace(self):
        """Returns True if all characters in this string are whitespace"""
        for char in self.chars:
            if not char.value.isspace():
                return False
        return True

    def isnumeric(self):
        """Returns true if all characters in the string are numeric"""
        for char in self.chars:
            if not char.value.isnumeric():
                return False
        return True

    def isalpha(self):
        """Returns true if all characters in the string are alphabetic (i.e. letters)"""
        for char in self.chars:
            if not char.value.isalpha():
                return False
        return True

    def isalnum(self):
        """Returns true if all characters in the string are alphanumeric (i.e. letters or numbers)"""
        for char in self.chars:
            if not char.value.isalnum():
                return False
        return True

    def __hash__(self):
        return hash(str(self))

    def __int__(self):
        """
        Converts the first character of this string into the hex value represented by it.
        Works for all hex digits (capital and lowercase).

        Raises:
            ValueError: if the first character is not a hex character
        """
        char = self.chars[0].value
        if '0' <= char <= '9':
            return ord(char) - ord('0')
        if 'a' <= char <= 'f':
            return ord(char) - ord('a') + 10
        if 'A' <= char <= 'F':
            return ord(char) - ord('A') + 10
        raise ValueError("invalid literal for int() with base 16: '" + char + "'")

    def __eq__(self, other):
        if type(other) == str:
            return str(self) == other
        if type(other) == String:
            return str(self) == str(other)
        return False

    def __lt__(self, other):
        assert type(other) == str or type(other) == String
        return str(self) < str(other)

    def __gt__(self, other):
        assert type(other) == str or type(other) == String
        return str(self) > str(other)

    def __le__(self, other):
        assert type(other) == str or type(other) == String
        return str(self) <= str(other)

    def __ge__(self, other):
        assert type(other) == str or type(other) == String
        return str(self) >= str(other)

    def __ne__(self, other):
        assert type(other) == str or type(other) == String
        return str(self) != str(other)

    def __add__(self, other):
        assert type(other) == String
        if type(other) == String:
            return String(self.chars + other.chars)

    def __iadd__(self, other):
        """
        iadd is the operator overload for inplace addition.
        i.e. s += c
        Works for other String objects and Character objects
        """
        assert type(other) == String
        if type(other) == String:
            self.chars += other.chars
        return self

    def __getitem__(self, key):
        """Returns the character located at the specified index, or the slice specified by the range"""
        if isinstance(key, slice):
            return String(self.chars[key])
        return String([self.chars[key]])

    def __delitem__(self, key):
        """Deletes the character located at the specified index, or the slice specified by the range"""
        if isinstance(key, slice):
            del self.chars[key]
        else:
            del self.chars[key]

    def __len__(self):
        """Returns the number of characters in this String"""
        return len(self.chars)

    def __str__(self):
        s = ''
        for i in self.chars:
            s += i.value
        return s

    def __repr__(self):
        return str(self)


def main():
    f = open("/Users/nicholasprowse/Desktop/mult.asm")
    code = LinedCode(f.read())
    f.close()
    print(code)

    print('done')


if __name__ == "__main__":
    main()
