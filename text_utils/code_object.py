from typing import Generic, TypeVar, Callable, Self

from .positioned_string import PositionedString

T = TypeVar('T')


class CodeObject(Generic[T], PositionedString):
    """
    This class represents some portion of code that is being compiled. It can be used to represent tokens, but can also
    be used to represent multiple tokens grouped together in the parsing phase. It contains the original code this
    object is derived from, stored in a PositionedString, so its location within the original code is known. It also
    contains a value attribute, which contains some value that represents the object (this will vary depending on its
    use). For example, value could be an integer for an integer token

    Attributes:
        text: The text, from the code, that this object derives from
        value: The value of this object. Optional attribute that describes the code
    """

    def __init__(self, value: T, text: PositionedString):
        super().__init__(text.text, text.coordinates)
        self.value = value

    @staticmethod
    def none(text=PositionedString.empty_string()):
        """
        Generates a CodeObject intended to represent a None value. The string associates with it is an empty string by
        default, but a custom string can be given
        Returns: A CodeObject representing None
        """
        return CodeObject(None, text)

    def __add__(self, other) -> Self:
        assert isinstance(other, PositionedString)
        return CodeObject(self.value, super().__add__(other))

    def __hash__(self) -> int:
        """Hashes are done based on the value attribute"""
        return hash(self.value)

    def __repr__(self) -> str:
        if self.value == self.text:
            return repr(self.value)
        return "(" + repr(self.value) + ", text=" + repr(self.text) + ')'


J = TypeVar('J')
K = TypeVar('K')
L = TypeVar('L')


def add(a: CodeObject[J], b: CodeObject[K], func: Callable[[J, K], L]) -> CodeObject[L]:
    return CodeObject(func(a.value, b.value), a + b)
