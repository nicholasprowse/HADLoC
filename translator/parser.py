from typing import Any

from error import CompilerException, ExceptionType
from grammar import Terminal, Sequential, optional, AnyOf, Repeated, TokenList
from translator.tokenizer import Token, TokenType


def token(arg: Any, name: str = None) -> Terminal:
    if isinstance(arg, TokenType):
        result = Terminal(lambda x: x.token_type == arg, name=name)
    else:
        result = Terminal(lambda x: x.value == arg, name=name)

    return result


def keyword(word: str):
    return Terminal(lambda x: x.value == word, error_name=f"'{word}' keyword")


class Parser:
    def __init__(self, tokens: list[Token]):
        self.tokens = tokens

        memory_segment = Sequential(
            token(TokenType.SEGMENT),
            token('['),
            token(TokenType.INTEGER),
            token(']'),
            name='memory segment'
        )

        function_definition = Sequential(
            keyword('function'),
            token(TokenType.IDENTIFIER, name='function name'),
            optional(token(TokenType.INTEGER, name='number of locals')),
            name='function definition'
        )

        function_call = Sequential(
            keyword('call'),
            token(TokenType.IDENTIFIER, name='function name'),
            optional(token(TokenType.INTEGER, name='number of arguments')),
            name='function call'
        )

        instruction = Sequential(
            AnyOf(function_definition, function_call),
            token(TokenType.INSTRUCTION_END),
        )

        program = Sequential(
            Repeated(instruction),
            token(TokenType.PROGRAM_END),
            name='program'
        )


        self.ast = program.match(TokenList(self.tokens))
        if self.ast is None:
            error = program.error
            raise CompilerException(ExceptionType.SYNTAX,
                                    self.tokens[error.token_offset],
                                    error.compile_error())