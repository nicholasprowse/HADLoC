from typing import Callable, Any, TypeVar

from hadloc.grammar.abstract_syntax_tree import ASTNode
from hadloc.grammar.token_list import TokenList

from abc import ABC, abstractmethod

T = TypeVar('T')


class GrammarException(Exception):
    """
    Let every terminal have an error message
    By default, the terminal parsing the last successful token determines the error
    However, if the last token is the first in a sequential or repeated symbol, then parsing of this symbol
    didn't even start -> show error for that symbol

    i.e.    Terminal fails: pass up it's error
            Repeated/Sequential fails: Pass up its own error only if no symbols were parsed, otherwise pass up the error
            of the first symbol that didn't parse
            AnyOf fails: Probably will work the same as the repeated/sequential

    Note:   Using these rules, an error on a sequential will only ever be used if it's parent is also a sequential,
        which will rarely happen. That is because, if the Sequential parsed no tokens, meaning it passes up it's error,
        then the parent (AnyOf or Repeated) will either use the error from another symbol that parsed more tokens, or
        use its own error, since no children parsed any tokens
            Similarly, a Repeated will only use its error if min_matches is non-zero, as a Repeated symbol cannot fail
            if min_matches is zero (but its children can fail, so their error could be used)

    Thus, Sequential rarely needs an error (only if its parent is also a Sequential), and Optional and ZeroOrMore never
    need an error
    """
    def __init__(self, msg: str, token_offset: int):
        self.token_offset = token_offset
        self.msg = msg


class GrammarSymbol(ABC):
    """
    A GrammarSymbol (often simply referred to as a symbol or grammar) is a set of rules that defined how a
    sequence of tokens should be parsed. Tokens can be parsed with a given grammar using the match method,
    which generates an ASTNode where the names match the symbols of the grammar

    Args:
        name: The name of the symbol
    """
    def __init__(self, name: str = None, error: str | Callable[[ASTNode], str] | None = None, auto_name: bool = False):
        self.name = name
        self.error_msg = error
        self.error: GrammarException | None = None
        self.auto_name = auto_name

    def assign_name(self, parent_node: ASTNode, match: Any):
        if not self.auto_name or parent_node.node_type is not None:
            return

        if not isinstance(match, ASTNode):
            parent_node.node_type = str(match)

        while True:
            if match.value is not None:
                parent_node.node_type = str(match.value)
                return
            match = match.children[0]

    def create_node(self) -> ASTNode:
        return ASTNode(self.name)

    def create_error(self, offset: int, parent_nodes: list[ASTNode]):
        if isinstance(self.error_msg, Callable):
            return GrammarException(self.error_msg(parent_nodes), offset)
        else:
            return GrammarException(self.error_msg if self.error_msg is not None else 'Unexpected token', offset)

    def process_error(self, error: GrammarException):
        if error is None:
            return

        if self.error is None or self.error.token_offset < error.token_offset:
            self.error = error

    @abstractmethod
    def match(self, tokens: TokenList[T], parent_nodes: list[ASTNode]) -> ASTNode[T] | None:
        """
        Use this method to test if the given list of tokens matches this symbol. It tests the tokens starting from the
        offset provided by the list. If the tokens do not match the symbol, None is returned, otherwise an ASTNode
        representing the parsed tokens with this grammar is returned
        Args:
            parent_nodes: All ASTNodes that are direct ancestors of the node being created. Needed for error generation
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

    def match(self, tokens: TokenList[T], parent_nodes: list[ASTNode]) -> ASTNode[T] | None:
        start_offset = tokens.offset
        node = self.create_node()
        for symbol in self.symbols:
            match = symbol.match(tokens, parent_nodes + [node])
            self.process_error(symbol.error)

            if match is not None:
                self.assign_name(node, match)
                node.add_child(match)
            else:
                tokens.offset = start_offset

                # If no symbols managed to parse past the current token, use this error, otherwise use the error from
                # the symbol that parsed the furthest
                if tokens.offset == self.error.token_offset:
                    self.error = self.create_error(tokens.offset, parent_nodes + [node])
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
    def __init__(self, symbol: GrammarSymbol, min_matches: int, max_matches: int | None, **kwargs):
        super().__init__(**kwargs)
        self.symbol = symbol
        self.min_matches = min_matches
        self.max_matches = max_matches

    def match(self, tokens: TokenList[T], parent_nodes: list[ASTNode]) -> ASTNode[T] | None:
        start_offset = tokens.offset
        node = self.create_node()
        num_matches = 0
        while self.max_matches is None or num_matches < self.max_matches:
            match = self.symbol.match(tokens, parent_nodes + [node])
            self.process_error(self.symbol.error)

            if match is not None:
                self.assign_name(node, match)
                node.add_child(match)
                num_matches += 1
            elif num_matches >= self.min_matches:
                return node
            else:
                tokens.offset = start_offset

                # If no symbols managed to parse past the current token, use this error, otherwise use the error from
                # the symbol that parsed the furthest
                if tokens.offset == self.error.token_offset:
                    self.error = self.create_error(tokens.offset, parent_nodes + [node])
                return None
        return node


class Optional(Repeated):
    def __init__(self, symbol: GrammarSymbol, **kwargs):
        super().__init__(symbol, 0, 1, **kwargs)


class ZeroOrMore(Repeated):
    def __init__(self, symbol: GrammarSymbol, **kwargs):
        super().__init__(symbol, 0, None, **kwargs)


class OneOrMore(Repeated):
    def __init__(self, symbol: GrammarSymbol, **kwargs):
        super().__init__(symbol, 1, None, **kwargs)


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

    def match(self, tokens: TokenList[T], parent_nodes: list[ASTNode]) -> ASTNode[T] | None:
        for symbol in self.symbols:
            match = symbol.match(tokens, parent_nodes)

            self.process_error(symbol.error)

            if match is not None:
                return match

        # If no symbols managed to parse past the current token, use this error, otherwise use the error from the
        # symbol that parsed the furthest
        if tokens.offset == self.error.token_offset:
            self.error = self.create_error(tokens.offset, parent_nodes)
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

    def match(self, tokens: TokenList[T], parent_nodes: list[ASTNode]) -> ASTNode[T] | None:
        token = tokens[0]
        if self.predicate(token):
            tokens.offset += 1
            node = ASTNode(self.name, token)
            self.assign_name(node, token)
            return node
        self.error = self.create_error(tokens.offset, parent_nodes)
        return None
