from typing import TypeVar, Generic

T = TypeVar('T')


class TokenList(Generic[T]):
    def __init__(self, tokens: list[T]):
        self.tokens = tokens
        self.offset = 0

    def __getitem__(self, item: int) -> T:
        return self.tokens[self.offset + item]
