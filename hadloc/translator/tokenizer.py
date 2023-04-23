import os
from enum import Enum
from io import TextIOWrapper
from typing import Optional

from hadloc import error

from hadloc.error import CompilerException, ExceptionType
from hadloc.text_utils import CodeObject, LinedCode, PositionedString
from hadloc.text_utils.positioned_string import Coordinate

keywords = ['add', 'sub', 'neg', 'and', 'or', 'not', 'eq', 'ne', 'gt', 'ge', 'lt', 'le', 'cry', 'in', 'push', 'pop',
            'label', 'if', 'goto', 'function', 'call', 'return', 'inc', 'dec']
segments = ['argument', 'local', 'static', 'constant', 'this', 'that', 'pointer', 'temp']

symbols = ['[', ']']


class TokenType(Enum):
    KEYWORD = 'keyword'
    SEGMENT = 'memory segment'
    IDENTIFIER = 'identifier'
    INTEGER = 'integer'
    SYMBOL = 'symbol'
    INSTRUCTION_END = 'line break'
    PROGRAM_END = 'program end'


class Token(CodeObject):
    def __init__(self, token_type: TokenType, value: CodeObject = CodeObject.none()):
        super().__init__(value.value, value)
        self.token_type = token_type


class Tokenizer:
    """
    Used for tokenizing a virtual machine file. Takes the raw text from the vm file as a string, and generates a 2
    dimensional list of tokens, stored in the variable tokens. The tokens list is structured so that each line in the
    code is in a separate row of the 2 dimensional list. Each row contains a series of tokens. Each token contains a
    token type and a value

    There are 5 types of token: 'keyword', 'segment', 'identifier', 'integer', 'instruction end'

    More information about what constitutes each type of token can be found in the documentation for the functions
    that tokenize them (e.g. Tokenizer.tokenize_label()).

    Args:
        file: An open file of the file to be tokenized. Must be in the mode 'r'

    Attributes:
        code (LinedCode): The code that is being tokenized. This object stored the current location within the text
            that is currently being tokenized.
        tokens: A two-dimensional list containing the tokens on each line. Each token is stored
            in a tuple containing the type of the token as a string, and the value of the token as a CodeObject

    Raises:
        CompilerException: If there is a syntax error in the assembly code, a Compiler exception will be raised
        containing the location and cause of the error
    """
    def __init__(self, file: TextIOWrapper):
        text = file.read()
        error.code = text.splitlines()
        CompilerException.file_name = os.path.realpath(file.name)
        self.code = LinedCode(text)
        self.tokens: list[Token] = []
        file.close()

    def run(self) -> list[Token]:
        """
        Performs the tokenization and returns the tokens as a list
        Returns: The list of tokens generated
        """
        # The code should be a series of alternating tokens and whitespace/comment sections. As such, we start by
        # advancing past any whitespace/comments at the start, before continuously tokenizing a token, and advancing
        # over whitespace/comment. If we advanced over a line when tokenizing a whitespace/comment, we must check if
        # there are more tokens before adding a new line, because we may have reached the end of the file.
        self.skip_whitespace_and_comments()
        while self.code.has_more():
            if self.tokenize_int() is None and \
                    self.tokenize_keyword_identifier() is None \
                    and self.tokenize_symbol() is None:
                raise CompilerException(ExceptionType.SYNTAX, self.code[0], 'Unexpected character')
            self.skip_whitespace_and_comments()

        self.end_instruction()
        self.tokens.append(Token(TokenType.PROGRAM_END))
        return self.tokens

    def addtoken(self, token_type: TokenType, text: PositionedString, value: Optional[int | str] = None) -> Token:
        """
        Helper function to add a new token at the same time as returning True. The text and value arguments are wrapped
        in a CodeObject. If value is not provided, it will be set to the value of text.

        Args:
            token_type: The type of the token
            text: The string from the code that generated the token
            value: The value of the token. This represents the value of the token. For example, if the token is an
                integer, value would be an int, that is the value of the token. If value is not passed, it gets set to
                text. This must be an int, or str type

        Returns: The token added
        """
        value = value if value is not None else text.text

        # Add INSTRUCTION_END if the new token is on a different line to the previous one
        if len(self.tokens) > 0 and self.tokens[-1].line() != text.line():
            self.end_instruction()

        self.tokens.append(Token(token_type, CodeObject(value, text)))
        return self.tokens[-1]

    def end_instruction(self):
        last_coord = self.tokens[-1].coordinates[-1]
        string = PositionedString(' ', [Coordinate(last_coord.line, last_coord.column + 1)])
        self.tokens.append(Token(TokenType.INSTRUCTION_END, CodeObject(None, string)))

    def skip_whitespace_and_comments(self):
        """
        Skips over any whitespace, and comments. Comments consist of any text between the '/*' and '*/' tokens, or
        any text after the '//' token but before the end of the line. May skip multiple lines
        """
        while True:
            if self.code[0].isspace():
                self.code.advance()

            elif self.code.match('//'):
                self.code.skip_line()

            elif self.code.match('/*'):
                comment_start = self.code.substring(length=2, end=0, relative=True)
                while self.code.advance_past('*/') is None:
                    if not self.code.skip_line():
                        raise CompilerException(ExceptionType.SYNTAX, comment_start, 'Comment not closed')

            elif not self.code.advance_line():
                return

    def tokenize_keyword_identifier(self) -> Token | None:
        """
        Tokenizes an instance of a command, segment or identifier. Will only tokenize one token.
        A keyword is one of:
            TODO add list of commands

        A segment represents a memory segment and is one of:
            ('argument', 'local', 'static', 'constant', 'this', 'that', 'pointer', 'temp')

        An identifier is any other sequence of alphanumeric characters or underscores, where the first character is
        not a numeric character.

        Returns: The token generated, or None if no token was created
        """
        word = self.code[0]
        if not word.isalpha() and not word == '_':
            return None

        for i in range(1, len(self.code)):
            if self.code[i].isalnum() or self.code[i] == '_':
                word += self.code[i]
            else:
                break

        self.code.advance(len(word))

        if word in keywords:
            return self.addtoken(TokenType.KEYWORD, word)

        if word in segments:
            return self.addtoken(TokenType.SEGMENT, word)

        return self.addtoken(TokenType.IDENTIFIER, word)

    def tokenize_symbol(self) -> Token | None:
        """
        Tokenizes a symbol. Allowed symbols are: '[', ']'

        Returns: The token generated, or None if no token was created
        """
        symbol = self.code.match(*symbols)
        if symbol is None:
            return None
        return self.addtoken(TokenType.SYMBOL, symbol)

    def tokenize_int(self) -> Token | None:
        """
        Tokenizes an integer. There are 5 types of integer: binary, octal, decimal, hexadecimal and characters.
        This only tokenizes the integer (not the sign). If there is a minus sign, it will be tokenized as a symbol, and
        the parser will compute the negative of this value. Character integers evaluate to the ASCII value of the
        character. The value of an integer token is a CodeObject whose value attribute is the integer represented
        by the token.

        Returns: The token generated, or None if no token was created
        """
        for function in [self.tokenize_bin, self.tokenize_hex,
                         self.tokenize_oct, self.tokenize_dec, self.tokenize_char]:
            token = function()
            if token is not None:
                return token

        return None

    def tokenize_bin(self) -> Token | None:
        """
        Tokenizes a binary integer.
        A binary integer must start with '0b' or '0B' and is followed by one or more '0's or '1's

        Returns: The token generated, or None if no token was created

        Raises:
            CompilerException: If the token starts with '0b' or '0B', but contains no binary digits directly after
        """
        start = self.code.offset
        if self.code.match('0b', '0B') is None:
            return None

        if self.code.match('0'):
            n = 0
        elif self.code.match('1'):
            n = 1
        else:
            raise CompilerException(ExceptionType.SYNTAX, self.code[0], "Invalid binary literal")

        while True:
            if self.code.match('0'):
                n *= 2
            elif self.code.match('1'):
                n = 2 * n + 1
            else:
                return self.addtoken(TokenType.INTEGER, self.code.substring(start=start), n)

    def tokenize_oct(self) -> Token | None:
        """
        Tokenizes an octal integer.
        An octal integer must start with '0' and then is followed by zero or more characters between '0' and '7'

        Returns: The token generated, or None if no token was created
        """
        start = self.code.offset
        if not self.code.match('0'):
            return None

        n = 0
        while True:
            char = self.code.match_range('0', '7')
            if char is not None:
                n = 8 * n + int(char)
            else:
                return self.addtoken(TokenType.INTEGER, self.code.substring(start=start), n)

    def tokenize_dec(self) -> Token | None:
        """
        Tokenizes a decimal integer.
        A decimal integer is a sequence of one or more characters between '0' and '9'

        Returns: The token generated, or None if no token was created
        """
        start = self.code.offset
        char = self.code.match_range('0', '9')
        if char is None:
            return None

        n = int(char)
        while True:
            char = self.code.match_range('0', '9')
            if char is not None:
                n = 10 * n + int(char)
            else:
                return self.addtoken(TokenType.INTEGER, self.code.substring(start=start), n)

    def tokenize_hex(self) -> Token | None:
        """
        Tokenizes a hexadecimal integer.
        A hexadecimal integer starts with '0x' or '0X' and then is followed by a sequence of one or more hexadecimal
        integers. A hexadecimal integer is any character between ('0' and '9'), ('a' and 'f') or ('A' and 'F')

        Returns: The token generated, or None if no token was created

        Raises:
            CompilerException: If the token starts with '0x' or '0X', but contains no hexadecimal digits directly after
        """
        start = self.code.offset
        if self.code.match('0x', '0X') is None:
            return None

        try:
            n = int(self.code[0])
            self.code.advance()
        except ValueError:
            raise CompilerException(ExceptionType.SYNTAX, self.code[0], "Invalid hex literal")

        while True:
            try:
                n = 16 * n + int(self.code[0])
                self.code.advance()
            except ValueError:
                return self.addtoken(TokenType.INTEGER, self.code.substring(start=start), n)

    def tokenize_char(self) -> Token | None:
        """
        Tokenizes a character integer.
        A character integer is a character with an ASCII value between 32 (space) and 126 (~) (inclusive), with a single
        quotation mark before and after it (').

        Returns: The token generated, or None if no token was created

        Raises:
            CompilerException:
                - If there is a single quotation mark at the start, but there is no closing quotation mark
                    in the correct place (i.e. with one character between the 2 quotation marks)
                - If the character inside the quotation marks is outside the ASCII range 32 to 126 (inclusive)
        """
        start = self.code.offset
        if not self.code.match("'"):
            return None

        if self.code[1] != "'":
            if self.code[0] == "'":
                raise CompilerException(ExceptionType.SYNTAX, self.code.substring(start=-1, end=1, relative=True),
                                        "Invalid character literal. Cannot have empty character literals")
            raise CompilerException(ExceptionType.SYNTAX, self.code.substring(start=-1, end=1, relative=True),
                                    "Invalid character literal. Character has no closing quotation mark")

        c = self.code[0].text
        self.code.advance(2)
        if 32 <= ord(c) <= 126:
            return self.addtoken(TokenType.INTEGER, self.code.substring(start=start), ord(c))
        else:
            raise CompilerException(
                ExceptionType.SYNTAX, self.code[-2],
                "Invalid character literal. Only characters with an ASCII value from 32 to 126 are allowed"
            )
