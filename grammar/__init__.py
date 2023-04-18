from .grammar import Terminal, Sequential, Repeated, AnyOf, GrammarSymbol, GrammarException
from .token_list import TokenList

def optional(symbol: GrammarSymbol, **kwargs) -> Repeated:
    return Repeated(symbol, min_matches=0, max_matches=1, **kwargs)