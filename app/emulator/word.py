from typing import Self


class Word:
    def __init__(self, val: int, bits: int = 8):
        self.bits = bits
        self.mask = (1 << self.bits) - 1
        self.val = val & self.mask
        self.carry = val > self.mask

    def concat(self, other: Self) -> Self:
        """
        Bitwise concatenation of two words. The number of bits in the resulting word is the sum of the number of bits
        in the two arguments
        Args:
            other: The word to concatenate to this one

        Returns:
            The concatenation of this word with the other word
        """
        return Word((self.val << other.bits) | other.val, bits=self.bits + other.bits)

    def __getitem__(self, index: int | slice):
        """
        Returns a word containing just the bits given by the slice. Does not support a step in the slice
        Args:
            index: The index or slice of the bits to extract

        Returns:
            The bits given by the slice
        """
        if type(index) == int:
            return Word((self.val >> index) & 0x1, bits=1)

        start = 0 if index.start is None else index.start
        stop = self.bits if index.stop is None else index.stop
        mask = ((1 << (stop - start)) - 1) << start
        return Word((self.val & mask) >> start, bits=stop - start)

    def msb(self) -> int:
        """
        Returns the index of the most significant non-zero bit of this word. Bits are indexed starting from 0 at the
        least significant bit. 0 is a special case in that there is no non-zero bit. In this case, -1 is returned
        Returns:
            The index of the most significant non-zero bit of this word
        """
        for i in range(self.bits - 1, -1, -1):
            if self[i]:
                return i
        return -1

    def __index__(self):
        return self.val

    def __eq__(self, other):
        if type(other) is Word:
            return self.val == other.val
        if type(other) is int:
            return self.val == other
        return False

    def __iadd__(self, other):
        other = other if type(other) is int else other.val
        self.val = (self.val + other) & self.mask
        return self

    def __add__(self, other):
        other = other if type(other) is int else other.val
        return Word(self.val + other, bits=self.bits)

    def __invert__(self):
        return Word(~self.val, bits=self.bits)

    def __and__(self, other):
        other = other if type(other) is int else other.val
        return Word(self.val & other, bits=self.bits)

    def __lt__(self, other):
        other = other if type(other) is int else other.val
        return self.val < other

    def __le__(self, other):
        other = other if type(other) is int else other.val
        return self.val <= other

    def __gt__(self, other):
        other = other if type(other) is int else other.val
        return self.val > other

    def __ge__(self, other):
        other = other if type(other) is int else other.val
        return self.val >= other

    def __repr__(self):
        return str(self)

    def __str__(self):
        return str(self.val)

    def __format__(self, format_spec):
        return format(self.val, format_spec)

    def __bool__(self):
        return self.val != 0
