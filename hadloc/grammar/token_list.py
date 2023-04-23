from typing import TypeVar, Generic

T = TypeVar('T')


class TokenList(Generic[T]):
    """
    Represents a generic list of token (could be any type of token), with an offset. Intended for use when matching a
    GrammarSymbol, which allows the matching to use the offset to keep track of where it is up to in the list of tokens
    """
    def __init__(self, tokens: list[T]):
        self.tokens = tokens
        self.offset = 0

    def __getitem__(self, index: int) -> T:
        """Returns the item in the list relative to the current offset. Use index of 0 to get the current item"""
        return self.tokens[self.offset + index]

    def has_more(self) -> bool:
        """Returns true if there are still more tokens to process"""
        return self.offset < len(self.tokens)
