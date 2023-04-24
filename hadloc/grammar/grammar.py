from typing import Callable, Any, TypeVar

from hadloc.error import CompilerException, ExceptionType
from .abstract_syntax_tree import ASTNode
from .token_list import TokenList

from abc import ABC, abstractmethod

T = TypeVar('T')
GrammarSymbolType = TypeVar('GrammarSymbolType', bound='GrammarSymbol')


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


class GrammarSymbol(ABC):
    """
    A GrammarSymbol (often simply referred to as a symbol or grammar) is a set of rules that defined how a
    sequence of tokens should be parsed. Tokens can be parsed with a given grammar using the match or parse method,
    both of which generate an ASTNode where the names match the symbols of the grammar. The match and parse methods
    differ in how they handle failure. If the tokens do not match the grammar, match returns None, while parse raises
    a CompilerException. The other main difference is that parse requires all tokens in the list to match, while match
    does not

    The symbols name determines the name of the node it produces. The name is optional and if it is unnamed (i.e. None),
    then the node generated will not be present in the final tree. However, all children will be, assuming they are
    named. This is useful if a symbol is required to enforce the grammar, but it wouldn't provide any useful information
    in the final tree

    The auto_name option allows a node to be automatically named based on the first node it parses. It is common for a
    symbol to start with a keyword, which notifies the parser which symbol is being parsed. In most cases, this keyword
    will be a suitable name for the symbol, so auto_name is very useful here, particularly if there are multiple
    options for the keyword. For example, the unary operation in the VM language
        Sequential(
            AnyOf(*[keyword(kw) for kw in ['neg', 'not', 'inc', 'dec']]),
            ...
            auto_name=True
        )
    In this case the node generated will be named one of 'neg', 'not', 'inc', 'dec' depending on which instruction it is

    When parsing/matching fails, the parsing algorithm automatically determines the token and grammar symbol that
    caused the failure, and using this information to generate a helpful error message. This relies on each symbol
    having a way to generate an error based on what has been parsed up to this point. Each symbol has an error
    parameter, which can be a fixed string, or a function. If it is a function, it receives a list of ASTNodes,
    containing all the direct ancestors of the node being generated at the time of failure, where the direct parent is
    the last element in the list. Assuming the grammar has been set up appropriately, this should provide complete
    information about the structure of the program up to the point of failure, providing extra context to the errors,
    and allowing for great flexibility in the generation of error messages.

    The way the error is chosen is based on what type of symbol fails. Each symbol contains an error message and error
    offset, representing the token offset where the error is.

    If a terminal fails to match, then it uses its error generator to set its error message and error offset.
    If any other type of symbol fails to match, then it checks the error messages and offsets of all the symbols it
    tried to match. The symbol with the highest offset determines the error offset. If the error offset is equal to the
    offset when matching that symbol started, then this symbol completely failed to parse (i.e. didn't successfully
    parse any tokens), so the error of this symbol is used. Otherwise, the error of the symbol that has the highest
    error offset is used.

    What this results in is this: The error message of a grammar symbol is used if matching on that symbol was attempted
    but no tokens where successfully parsed.

    allows for intelligent error messages based on

    Args:
        name: The name of the symbol. This will be used to name the ASTNode this symbol generates. If a symbol is
            unnamed (i.e. None), then the node this symbol generates will not directly appear in the final tree,
            however its children will (assuming they have a name)
        error: the error to display if the parsing fails on this symbol. Can be a raw string, resulting in a fixed
            error, or a function. If a function is provided, the argument to the function will be a list of ASTNodes
            that are the direct ancestors to the node this grammar would have created. This list can provide extra
            context to the error, allowing you to customise the error based on previous tokens. The error is optional
            and if not provided, a default error is used instead
        auto_name: whether this grammar should automatically name itself from the first token it matches or not
    """
    def __init__(self,
                 name: str = None,
                 error: str | Callable[[list[ASTNode]], str] | None = None,
                 auto_name: bool = False):
        self.name = name
        self.error_msg = ''
        self.error_offset = 0
        self.auto_name = auto_name

        if isinstance(error, str):
            self.error_generator = lambda nodes: error
        elif error is None:
            self.error_generator = lambda nodes: 'Unexpected token'
        else:
            self.error_generator = error

    def create_error(self, error_offset: int, parent_nodes: list[ASTNode]):
        """Helper function to set the error. Just sets the error offset and error message based on the arguments"""
        self.error_offset = error_offset
        self.error_msg = self.error_generator(parent_nodes)

    def process_error(self, symbol: GrammarSymbolType):
        """
        Used to determine if the error from a matched symbol should be pulled to this symbol. This should be called
        during matching, everytime a match is attempted with another symbol. After attempting to match the symbol,
        call this method with the symbol. If the symbols error offset is larger than this errors offset, then the
        error data from the symbol is copied to this symbol (i.e. copy error if the symbol parsed further than any
        others yet)

        Args:
            symbol: The symbol that was attempted to match against (whether it was successful or not)
        """
        if self.error_offset < symbol.error_offset:
            self.error_offset = symbol.error_offset
            self.error_msg = symbol.error_msg

    def parse(self, tokens: list[T]) -> ASTNode[T]:
        """
        Parses a given list of tokens according to this grammar. Similar to the match method, however it is intended
        for the top level grammar that should match the entire list of tokens. It determines if the list of tokens
        matches the grammar and generates an ASTNode representing the tokens. However, if the tokens do not match the
        grammar, it raises a CompilerException with the token that caused the failure, along with the error message
        provided by the GrammarSymbol where the failure occurred. Also, unlike the match method, this method requires
        the entire token list to match the grammar. If the entire token list is not consumed during parsing,
        then a CompilerException is raise with the same information about where the matching failed Args: tokens:
        List of tokens to parse

        Returns: The ASTNode representing the structure of the program according to this grammar

        Raises:
            CompilerException: If the token list does not completely match the grammar
        """
        token_list = TokenList(tokens)
        ast = self.match(token_list, [])
        if ast is None or token_list.offset < len(tokens):
            raise CompilerException(ExceptionType.SYNTAX, tokens[self.error_offset], self.error_msg)
        return ast

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
        *symbols: The symbols to match in sequential order
        **kwargs: keyword arguments provided to the GrammarSymbol implementation (name, error, auto_name)
    """
    def __init__(self, *symbols: GrammarSymbol, **kwargs):
        super().__init__(**kwargs)
        self.symbols = symbols

    def match(self, tokens: TokenList[T], parent_nodes: list[ASTNode]) -> ASTNode[T] | None:
        start_offset = tokens.offset
        node = ASTNode(self.name, self.auto_name)
        for symbol in self.symbols:
            match = symbol.match(tokens, parent_nodes + [node])
            self.process_error(symbol)

            if match is not None:
                node.add_child(match)
            else:
                tokens.offset = start_offset

                # If no symbols managed to parse past the current token, use this error, otherwise use the error from
                # the symbol that parsed the furthest
                if tokens.offset == self.error_offset:
                    self.create_error(tokens.offset, parent_nodes + [node])
                return None
        return node


class Repeated(GrammarSymbol):
    """
    A repeated grammar matches a given symbol multiple times, where it must match at least min_matches times, and
    at most max_matches times. If max_matches is None, then this will match as many symbols as possible.

    If the given symbol matches fewer than min_matches times, then matching fails, and None is returned.
    However, if the symbol matches more than max_matches times, then matching will succeed, but only max_matches
    symbols will be parsed
    Args:
        symbol: The symbol to match
        min_matches: The minimum number of times the symbol must be matched
        max_matches: The maximum number of times the symbol must be matched
        **kwargs: keyword arguments provided to the GrammarSymbol implementation (name, error, auto_name)
    """
    def __init__(self, symbol: GrammarSymbol, min_matches: int, max_matches: int | None, **kwargs):
        super().__init__(**kwargs)
        self.symbol = symbol
        self.min_matches = min_matches
        self.max_matches = max_matches

    def match(self, tokens: TokenList[T], parent_nodes: list[ASTNode]) -> ASTNode[T] | None:
        start_offset = tokens.offset
        node = ASTNode(self.name, self.auto_name)
        num_matches = 0
        while self.max_matches is None or num_matches < self.max_matches:
            match = self.symbol.match(tokens, parent_nodes + [node])
            self.process_error(self.symbol)

            if match is not None:
                node.add_child(match)
                num_matches += 1
            elif num_matches >= self.min_matches:
                return node
            else:
                tokens.offset = start_offset

                # If no symbols managed to parse past the current token, use this error, otherwise use the error from
                # the symbol that parsed the furthest
                if tokens.offset == self.error_offset:
                    self.create_error(tokens.offset, parent_nodes + [node])
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


class OneOf(GrammarSymbol):
    """
    Represents a grammar that will match any one of the given symbols. If the tokens match more than one of the provided
    symbols, then it will match with the first one in the provided list

    Args:
        *matches: All the symbols this could match with
        **kwargs: keyword arguments provided to the GrammarSymbol implementation (name, error, auto_name)
    """
    def __init__(self, *symbols: GrammarSymbol, **kwargs):
        super().__init__(**kwargs)
        self.symbols = symbols

    def match(self, tokens: TokenList[T], parent_nodes: list[ASTNode]) -> ASTNode[T] | None:
        for symbol in self.symbols:
            match = symbol.match(tokens, parent_nodes)
            self.process_error(symbol)

            if match is not None:
                return match

        # If no symbols managed to parse past the current token, use this error, otherwise use the error from the
        # symbol that parsed the furthest
        if tokens.offset == self.error_offset:
            self.create_error(tokens.offset, parent_nodes)
        return None


class Terminal(GrammarSymbol):
    """
    A terminal matches a single token based on the predicate given. Since the token list could be of any type, a
    predicate function is used to determine what matches. The predicate takes a token as an argument, and returns
    True or False depending on if it matches the token

    Args:
        predicate: A function with a token as argument that returns True if the token should match the symbol
        **kwargs: keyword arguments provided to the GrammarSymbol implementation (name, error, auto_name)
    """
    def __init__(self, predicate: Callable[[Any], bool], **kwargs):
        super().__init__(**kwargs)
        self.predicate = predicate

    def match(self, tokens: TokenList[T], parent_nodes: list[ASTNode]) -> ASTNode[T] | None:
        if not tokens.has_more():
            return None
        token = tokens[0]
        if self.predicate(token):
            tokens.offset += 1
            node = ASTNode(self.name, self.auto_name, token)
            return node
        self.create_error(tokens.offset, parent_nodes)
        return None
