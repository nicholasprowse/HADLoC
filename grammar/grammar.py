from typing import Callable, Any, TypeVar

from grammar.abstract_syntax_tree import ASTNode
from grammar.token_list import TokenList

from abc import ABC, abstractmethod

T = TypeVar('T')

class GrammarException(Exception):
    """
    Types of Exceptions
    Unexpected Token: unable to parse, but didn't get further than one token into any grammar
    Invalid {name of parent grammar}. Expected {name of terminal}: Terminal missing from Sequential
    Invalid {name of parent grammar}. Expected optional {name of terminal}: optional terminal wrong in sequential

    """
    def __init__(self, symbol, token_offset: int):
        self.token_offset = token_offset
        self.symbols = [symbol]

    def compile_error(self) -> str:
        name = self.symbols[0].error_name
        if name is None:
            return 'Unexpected token'

        parent, parent_index = None, -1
        for i, symbol in enumerate(self.symbols[1:]):
            if symbol.name is not None:
                parent = symbol
                parent_index = i + 1
                break

        name_before = ''
        if isinstance(parent, Sequential):
            child_index = parent.symbols.index(self.symbols[parent_index - 1])
            if child_index > 0:
                name_before = f' after {parent.symbols[child_index - 1].error_name}'

        return f'Invalid {parent.name}. Expected {name}{name_before}'

class GrammarSymbol(ABC):
    """
    A GrammarSymbol (often simply referred to as a symbol or grammar) is a set of rules that defined how a
    sequence of tokens should be parsed. Tokens can be parsed with a given grammar using the match method,
    which generates an ASTNode where the names match the symbols of the grammar

    Args:
        name: The name of the symbol
    """
    def __init__(self, name: str = None, error_name: str = None):
        self.name = name
        self.error: GrammarException | None = None
        self.error_name = error_name if error_name is not None else name

    def create_node(self) -> ASTNode:
        return ASTNode(self.name)

    def process_error(self, error: GrammarException):
        if error is None:
            return

        if self.error is None or self.error.token_offset < error.token_offset:
            self.error = error
            self.error.symbols.append(self)

    @abstractmethod
    def match(self, tokens: TokenList[T]) -> ASTNode[T] | None:
        """
        Use this method to test if the given list of tokens matches this symbol. It tests the tokens starting from the
        offset provided by the list. If the tokens do not match the symbol, None is returned, otherwise an ASTNode
        representing the parsed tokens with this grammar is returned
        Args:
            tokens: The list of tokens to match

        Returns: An ASTNode representing the parsed tokens, or None if the tokens don't match
        """
        pass


class Sequential(GrammarSymbol):
    """
    Matches all the given symbols sequentially, in the order given. If any one symbols doesn't match, this entire
    symbol doesn't match

    Args:
        name: The name of this symbol.
        symbols: The symbols to match
    """
    def __init__(self, *symbols: GrammarSymbol, **kwargs):
        super().__init__(**kwargs)
        self.symbols = symbols


    def match(self, tokens: TokenList[T]) -> ASTNode[T] | None:
        start_offset = tokens.offset
        node = self.create_node()
        for symbol in self.symbols:
            match = symbol.match(tokens)
            self.process_error(symbol.error)

            if match is not None:
                node.add_child(match)
            else:
                tokens.offset = start_offset
                return None
        return node

class Repeated(GrammarSymbol):
    """
    A repeated grammar matches a given symbol multiple times, where it must match at least min_matches times, and
    at most max_matches times. If max_matches is None, then this will match as many symbols as possible. This can
    also be used to create an optional symbol by using min_matches=0, max_matches=1.

    If the given symbol matches fewer than min_matches times, then matching fails, and None is returned.
    However, if the symbol matches more than max_matches times, then matching will succeed, but only max_matches
    symbols will be parsed
    Args:
        name: The name of this symbol.
        symbol: The symbol to match
        min_matches: The minimum number of times the symbol must be matched
        max_matches: The maximum number of times the symbol must be matched
    """
    def __init__(self, symbol: GrammarSymbol, min_matches: int = 0, max_matches: int | None = None, **kwargs):
        super().__init__(**kwargs)
        self.symbol = symbol
        self.min_matches = min_matches
        self.max_matches = max_matches

    def match(self, tokens: TokenList[T]) -> ASTNode[T] | None:
        start_offset = tokens.offset
        node = self.create_node()
        num_matches = 0
        while self.max_matches is None or num_matches < self.max_matches:
            match = self.symbol.match(tokens)
            self.process_error(self.symbol.error)
            # if self.error is None or self.error.token_offset < self.symbol.error.token_offset:
            #     if self.symbol.error is not None:
            #         self.error = self.symbol.error
            #         self.error.names.append(self.name)
            #         grammar_type = f'repeated {self.min_matches} to {self.max_matches}'
            #         if self.min_matches == 0 and self.max_matches == 1:
            #             grammar_type = 'optional'
            #         elif self.min_matches == 0 and self.max_matches is None:
            #             grammar_type = 'zero or more'
            #         elif self.min_matches == 1 and self.max_matches is None:
            #             grammar_type = 'one or more'
            #         elif self.max_matches is None:
            #             grammar_type = f'{self.min_matches} or more'
            #         self.error.types.append(grammar_type)

            if match is not None:
                node.add_child(match)
                num_matches += 1
            elif num_matches >= self.min_matches:
                return node
            else:
                tokens.offset = start_offset
                return None
        return node


class AnyOf(GrammarSymbol):
    """
    Represents a grammar that will match any of the given symbols. If the tokens match more than one of the provided
    symbols, then it will match with the first one in the provided list
    Args:
        name: Name of this symbol
        *matches: All the symbols this could match with
    """
    def __init__(self, *symbols: GrammarSymbol, **kwargs):
        super().__init__(**kwargs)
        self.symbols = symbols

    def match(self, tokens: TokenList[T]) -> ASTNode[T] | None:
        for symbol in self.symbols:
            match = symbol.match(tokens)
            self.process_error(symbol.error)

            if match is not None:
                return match
        return None


class Terminal(GrammarSymbol):
    """
    A terminal matches a single token based on the arguments given. Both the value and token_type must be equal to the
    token for it to match. If either value or token_type are None, then that parameter will match with anything.
    i.e. Terminal(token_type=TokenType.Identifier) will match any identifier regardless of the value
    """
    def __init__(self, predicate: Callable[[Any], bool], **kwargs):
        super().__init__(**kwargs)
        self.predicate = predicate

    def match(self, tokens: TokenList[T]) -> ASTNode[T] | None:
        token = tokens[0]
        if self.predicate(token):
            tokens.offset += 1
            return ASTNode(self.name, token)
        self.error = GrammarException(self, tokens.offset)
        return None
