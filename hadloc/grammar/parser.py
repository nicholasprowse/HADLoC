from hadloc.error import CompilerException, ExceptionType
from .grammar import GrammarSymbol
from .token_list import TokenList


def parse(grammar: GrammarSymbol, tokens: list):
    ast = grammar.match(TokenList(tokens), [])
    if ast is None:
        raise CompilerException(ExceptionType.SYNTAX, tokens[grammar.error.token_offset], grammar.error.msg)
    return ast
