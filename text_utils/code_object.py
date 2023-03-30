from typing import Self, Any, Callable

from .positioned_string import PositionedString


class CodeObject:
    """
    This class represents some portion of code that is being compiled. It can be used to represent tokens, but can also
    be used to represent multiple tokens grouped together in the parsing phase. It contains the original code this
    object is derived from, stored in a PositionedString, so its location within the original code is known. It also
    contains a value attribute, which contains some value that represents the object (this will vary depending on its
    use). For example, value could be an integer for an integer token. Many operators (such as addition) are overloaded.
    If the other argument is a CodeObject, the operation is applied to the value, and the two PositionObjects are added
    together.

    Attributes:
        text (PositionedString): The text, from the code, that this object derives from
        value (any): The value of this object. Optional attribute that describes the code
    """

    def __init__(self, value: Any, text: PositionedString):
        self.value = value
        self.text = text

    def binary_operator(self, other: Any, operator: Callable[[Any], Any]) -> Self:
        if isinstance(other, CodeObject):
            return CodeObject(operator(other.value), self.text + other.text)
        else:
            return CodeObject(operator(other), self.text)

    def __eq__(self, other) -> Self:
        """
        Tests if this object is equal to the other. When checking for equality, only the value attribute is checked.

        Args:
            other: The other object to test equality

        Returns:
            True if the value attribute equals the other object, otherwise False
        """
        return self.binary_operator(other, lambda x: self.value == x)

    def __lt__(self, other) -> Self:
        """
        Tests if this object is less than the other. Only the value attribute is relevant.

        Args:
            other: The other object to test equality

        Returns:
            True if the value attribute is less than the other object, otherwise False
        """
        return self.binary_operator(other, self.value.__lt__)

    def __gt__(self, other) -> Self:
        """
        Tests if this object is greater than to the other. Only the value attribute is relevant.

        Args:
            other: The other object to test equality

        Returns:
            True if the value attribute is greater than the other object, otherwise False
        """
        return self.binary_operator(other, self.value.__gt__)

    def __le__(self, other) -> Self:
        """
        Tests if this object is less than or equal to the other. Only the value attribute is relevant.

        Args:
            other: The other object to test equality

        Returns:
            True if the value attribute is less than the other object, otherwise False
        """
        return self.binary_operator(other, self.value.__le__)

    def __ge__(self, other) -> Self:
        """
        Tests if this object is greater than or equal to the other. Only the char attribute is relevant.

        Args:
            other: The other object to test equality

        Returns:
            True if the value attribute is greater than the other object, otherwise False
        """
        return self.binary_operator(other, self.value.__ge__)

    def __ne__(self, other) -> Self:
        """
        Tests if this object is not equal to the other. Only the char attribute is relevant.

        Args:
            other: The other object to test equality

        Returns:
            True if the value attribute is not equal to the other object, otherwise False
        """
        return self.binary_operator(other, self.value.__ne__)

    def __and__(self, other) -> Self:
        """
        Bitwise and for CodeObject. Ands together the two value properties,
        and adds together the text properties
        """
        return self.binary_operator(other, self.value.__and__)

    def __or__(self, other) -> Self:
        """
        Bitwise or for CodeObject. Ors together the two value properties,
        and adds together the text properties
        """
        return self.binary_operator(other, self.value.__or__)

    def __add__(self, other) -> Self:
        """
        Addition for CodeObject. Adds together the two value properties,
        and adds together the text properties
        """
        return self.binary_operator(other, self.value.__add__)

    def __sub__(self, other: int) -> Self:
        """
        Subtraction for CodeObject. Subtracts the two value properties,
        and adds together the text properties
        """
        return self.binary_operator(other, self.value.__sub__)

    def __lshift__(self, other: int) -> Self:
        """
        Left shift operator for CodeObject. Left shifts this CodeObjects value by the value provided in the argument,
        and adds together the text properties
        """
        return self.binary_operator(other, self.value.__lshift__)

    def __rshift__(self, other: int) -> Self:
        """
        Right shift operator for CodeObject. Right shifts this CodeObjects value by the value provided in the argument,
        and adds together the text properties
        """
        return self.binary_operator(other, self.value.__rshift__)

    def __hash__(self) -> int:
        """Hashes are done based on the value attribute"""
        return hash(self.value)

    def __invert__(self) -> Self:
        """Returns the bitwise inverse of the value of this CodeObject, as a CodeObject"""
        return CodeObject(~self.value, self.text)

    def __neg__(self) -> Self:
        """Returns the negative of the value of this CodeObject, as a CodeObject"""
        return CodeObject(-self.value, self.text)

    def __str__(self) -> str:
        return str(self.value)

    def __repr__(self) -> str:
        if self.value == self.text:
            return repr(self.value)
        return "(" + repr(self.value) + ", text=" + repr(self.text) + ')'

    def __bool__(self) -> bool:
        return bool(self.value)

    def __len__(self) -> int:
        """Returns the length of the value attribute"""
        return len(self.value)