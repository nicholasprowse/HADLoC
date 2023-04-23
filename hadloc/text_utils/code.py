from .positioned_string import PositionedString


class Code:
    """
    A Code object is used to tokenize text. It is a string of text, and contains an integer offset. Whenever
    characters are indexed, they are indexed relative to this offset. The offset can be advanced in different ways,
    allowing a tokenizer to traverse through some text, without needing to save the position it is up to.
    The text is stored in a PositionedString object, meaning each character has source code coordinate attached
    to it. This allows one to edit/substring the text, while still having a reference to where each character came from
    in the original text.

    No errors are thrown if characters are accessed which are out of range. Instead, if one attempts to access a
    character out of range of the text, then the null character is returned.

    Args:
        text: The raw text of the code

    Attributes:
        text: PositionedString containing the code to be processed
        offset: The index of the current character being processed. All functions requiring indices, are indexed
        relative to this offset
    """

    def __init__(self, text: str):
        self.offset = 0
        self.text = PositionedString.create_string(text)

    def substring(self, start: int | None = None, end: int | None = None,
                  length: int | None = None, relative: bool = False) -> PositionedString:
        """
        Returns a substring with the given parameters. The substring can be specified using a start, end or length.
        If either of start or end are not provided, they are determined based on length, or, if length isn't provided
        they default to the current offset. If length is not provided, then the length is determined based on the
        start and end values. Only two of start, end and length are required to specify a substring, so if all three
        are provided, an error is raised as this can lead to contradictions.

        If relative is true, then the substring indices are relative to the current offset, otherwise they are relative
        to the start of the text.

        If the substring extends past the end of the text, no error will be raised. Instead, the result will just be
        shorter than expected

        Args:
            start: the start index of the substring (inclusive)
            end: the end index of the substring (exclusive)
            length: the length of the substring
            relative: if true, indices are relative to the current offset

        Returns: the substring specified by the arguments
        """
        assert start is None or end is None or length is None
        default = 0 if relative else self.offset
        if start is None:
            start = default if end is None or length is None else end - length
        if end is None:
            end = default if length is None else start + length
        if relative:
            start += self.offset
            end += self.offset
        return self.text[start:min(end, len(self.text))]

    def has_more(self) -> bool:
        """Returns True if there are more characters left to process"""
        return self.offset < len(self.text)

    def advance(self, amount: int = 1) -> PositionedString:
        """
        Increments the offset by a given amount, and returns a substring of the String advanced past

        Args:
            amount: amount to advance

        Returns: substring of the string advanced past
        """
        temp = self.substring(length=amount, relative=True)
        self.offset += len(temp)
        return temp

    def advance_past(self, match: str) -> PositionedString | None:
        """
        Advances past the first occurrence of the given string. If no occurrence of match exists in the string, then no
        text will be advanced past, and None will be returned

        Args:
            match: string to find the first occurrence of
        Returns:
            If match was found, returns a PositionedString containing the text advanced past. Otherwise, returns None.
        """
        for i in range(self.offset, len(self.text)):
            if self.text[i: i + len(match)] == match:
                temp = self.text[self.offset: i + len(match)]
                self.offset = i + len(match)
                return temp

        return None

    def match(self, *matches: str) -> PositionedString | None:
        """
        If the text immediately following the current offset matches any of the given strings, it is advanced
        past, and the matching string is returned. Otherwise, None is returned and nothing is advanced past.

        Args:
            *matches: The string to check for
        Returns: The matching string if one of the given string is advanced past, otherwise, None
        """
        for match in matches:
            sub = self.substring(length=len(match), relative=True)
            if sub == match:
                self.offset += len(match)
                return self.substring(end=0, length=len(match), relative=True)
        return None

    def match_range(self, lower: chr, upper: chr) -> PositionedString | None:
        """
        If the character at the current offset is inbetween the lower and upper characters provided (inclusive), then
        this character is advanced past and the character is returned. Otherwise, None is returned
        Args:
            lower: the lower end of the range to check
            upper: the upper end of the range to check

        Returns:
            If the current character is in the given range, then the character is returned, otherwise None is returned
        """
        if self.offset < len(self.text) and lower <= self[0] <= upper:
            self.offset += 1
            return self.text[self.offset - 1]
        return None

    def __len__(self) -> int:
        """Returns the length of the code after (and including the offset)"""
        return max(0, len(self.text) - self.offset)

    def __getitem__(self, item):
        """
        Returns the character at the given location, relative to the offset.
        If the requested item is out of range, the null character will be returned, with the position of the final
        character.
        """
        try:
            return self.text[item + self.offset]
        except IndexError:
            last_char = self.text[-1]
            return PositionedString('\0', last_char.coordinates)

    def __str__(self) -> str:
        return str(self.text[self.offset:])

    def __repr__(self) -> str:      # pragma: no cover
        return str(self)


class LinedCode(Code):
    """
    Behaves exactly the same as a Code object, but it respects line boundaries. At any time, the Code object behaves as
    though all that exists is the current line. For example, if you try to substring beyond a line boundary, all you
    will get is the text on the current line. Similarly, you cannot advance past a line boundary using the advance or
    match functions. The object is only 'aware' of the current line. has_more, advance_line and skip_line are the only
    functions that are 'aware' of text beyond the current line. Use skip_line to unconditionally move to the next line,
    while advance_line can be used to move to the next line if and only if the current line is complete

    Args:
        text : The text of the code. Trailing and leading whitespace on each line will be removed

    Attributes:
        remaining_text: Text that is yet to be processed. The text attribute contains just the line being processed
            now, while remaining_text contains everything after that
    """

    def __init__(self, text: str):
        super().__init__(text)
        self.remaining_text: PositionedString = self.text
        self.skip_line()

    def advance_line(self) -> bool:
        """
        Advances onto the next line if and only if the current line is completed

        Returns: True if a line was advanced past, otherwise False
        """
        if super().has_more():
            return False

        return self.skip_line()

    def skip_line(self) -> bool:
        """
        Similar to advance_line(), but will move onto the next line regardless of whether the current line is completed
        or not. If the current line is not completed, any unprocessed text will be skipped over. Useful for skipping
        past comments
        Returns: True if a line was skipped and False otherwise. False return indicates the end of the code. If False
            is returned, the current line is still advanced past, it just means that it didn't advance to the next line
            because there isn't a next line
        """
        if len(self.remaining_text) == 0:
            self.offset = len(self.text)
            return False

        self.offset = 0
        line_number = self.remaining_text.line()
        if line_number == self.remaining_text.line(-1):
            self.text = self.remaining_text
            self.remaining_text = PositionedString.empty_string()
            return True

        for i, char in enumerate(self.remaining_text):
            if char.line() != line_number:
                self.text = self.remaining_text[:i]
                self.remaining_text = self.remaining_text[i:]
                return True

    def has_more(self) -> bool:
        """Returns True if there are more characters left to process"""
        return super().has_more() or len(self.remaining_text) > 0
