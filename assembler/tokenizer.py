import os
import error

from error import CompilerException
from cstring import LinedCode, CodeObject

keywords = ['lda', 'ldb', 'ldu', 'mov', 'jmp', 'jlt', 'jeq', 'jgt', 'jle', 'jge', 'jne', 'nop', 'jis', 'jcs', 'opd',
            'opi', 'hlt', 'not', 'neg', 'inc', 'dec', 'sub', 'and', 'or', 'add', 'ics', 'icc', 'define']

registers = ['L', 'H', 'M', 'I', 'X', 'Y']

symbols = [':', '+', '-', '&', '|', '!', '(', ')']


class Tokenizer:
    """
    Tokenizes an assembly file. Takes the raw text from the assembly file as a string, and generates a 2 dimensional
    list of tokens, stored in the variable tokens. The tokens list is structured so that each line in the code is
    in a seperate row of the 2 dimensional list. Each row contains a series of tokens, stored as tuples. The first
    element of the tokens is the type of the token, stored as a string, and the second element is the value.

    There are 5 types of token: 'keyword', 'identifier', 'register', 'label', 'integer'

    More information about what constututes each type of token can be fould in the documentation for the functions
    that tokenize them (e.g. Tokenizer.tokenize_label()).

    The value of the token is stored as a CodeObject. This CodeObject stores both the value of the token, and the
    original text that created the token as a PositionedString. This means that if an error is created, we can determine
    exactly where that token was in the code.

    Args:
        text (str): the raw text to be tokenized, obtained from the assembly file, stored as a string

    Attributes:
        code (LinedCode): The code that is being tokenized. This object stored the current location within the text
            that is currently being tokenized.
        tokens (list<list<tuple>>): A two dimensional list containing the tokens on each line. Each token is stored
            in a tuple containing the type of the token as a string, and the value of the token as a CodeObject

    Raises:
        CompilerException: If there is a syntax error in the assembly code, a Compiler exception will be raised
        containing the location and cause of the error
    """
    def __init__(self, text):
        self.code = LinedCode(text)
        # tokens = (type, value)
        self.tokens = [[]]

        # The code should be a series of alternating tokens and whitespace/comment sections. As such, we start by
        # advancing past any whitespace/comments at the start, before continouosly tokenizing a token, and advancing
        # over whitespace/comment. If we advanced over a line when tokenizing a whitespace/comment, we must check if
        # there are more tokens before adding a new line, because we may have reached the end of the file.
        self.skip_whitespace_and_comments()
        while self.code.hasmore():
            if not (self.tokenize_int() or self.tokenize_keyword_identifier_register() or self.tokenize_symbol()):
                raise CompilerException(CompilerException.SYNTAX, 'Unexpected character', self.code[0])

            if self.skip_whitespace_and_comments():
                if self.code.hasmore():
                    self.tokens.append([])

    def addtoken(self, tokentype, text, value=None):
        """
        Helper function to add a new token at the same time as returning True. The text and value arguments are wrapped
        in a CodeObject. If value is not provided, it will be set to the value of text.

        Args:
            tokentype (str): The type of the token.
                Must be one of 'keyword', 'identifier', 'register', 'label', 'integer'
            text (PositionedString): The string from the code that generated the token
            value: The value of the token. This represents the value of the token. For example, if the token is an
                integer, value would be an int, that is the value of the token. If value is not passed, it gets set to
                text

        Returns:
            (bool): True
        """
        if value is None:
            value = text
        self.tokens[-1].append((tokentype, CodeObject(value, text)))
        return True

    def skip_whitespace_and_comments(self):
        """
        Skips over any whitespace, and comments. Comments consist of any text between the '/*' and '*/' tokens, or
        any text after the '//' token but before the end of the line. May skip multiple lines. If any line breaks are
        skipped over, True is returned, otherwise, False is returned
        Returns:
            True if a line break was advanced over, False otherwise
        """
        skippedline = False
        should_continue = True
        while should_continue:
            should_continue = False
            while self.code[0].isspace():
                should_continue = True
                self.code.advance()

            if self.code.match('//'):
                should_continue = True
                # Move offset to end of the current line
                current_line = self.code.current_line()
                current_line.advance(len(current_line))

            comment_start = self.code.substring_length(2)
            if self.code.match('/*'):
                should_continue = True
                while self.code.current_line().advancepast('*/') is None:
                    skippedline = True
                    if self.code.line < len(self.code.lines) - 1:
                        self.code.line += 1
                    else:
                        raise CompilerException(error.CompilerException.SYNTAX, 'Comment not closed', comment_start)

            if self.code.advanceline():
                should_continue = True
                skippedline = True

        return skippedline

    def tokenize_keyword_identifier_register(self):
        """
        Tokenizes an intance of a keyword, identifer or register. Will only tokenize one token.
        A keyword is one of:
            ('lda', 'ldb', 'mov', 'jmp', 'jlt', 'jeq', 'jgt', 'jle', 'jge', 'jne', 'nop', 'jcs', 'jis', 'opd',
            'opi', 'hlt', 'not', 'neg', 'inc', 'dec', 'sub', 'and', 'or', 'add', 'icc', 'ics', 'define')

        A register is one of:
            ('L', 'H', 'M', 'I', 'X', 'Y')

        An identifer is any other sequence of alphanumeric characters or underscores, where the first character is
        not a numeric character.

        Returns:
            (bool): True if a keyword, identifier or register token was created, False otherwise
        """
        word = self.code[0]
        if not (word.isalpha() or word == '_'):
            return False

        for i in range(1, len(self.code)):
            if self.code[i].isalnum() or self.code[i] == '_':
                word += self.code[i]
            else:
                break

        self.code.advance(len(word))

        if word in keywords:
            return self.addtoken('keyword', word)

        if word in registers:
            return self.addtoken('register', word)

        return self.addtoken('identifier', word)

    def newline(self):
        """
        Checks if the end of the current line has been reached, and if it has, moves onto the next line, and
        cretes a new line in the tokens list. Returns True if a new line was advanced over, False otherwise.

        Returns:
            (bool): True if a new line was advanced over, False otherwise
        """
        if self.code.advanceline():
            self.tokens.append([])
            return True
        return False

    def tokenize_symbol(self):
        """
        Tokenizes a symbol. There are five symbols: '+', '-', '&', '|', '!', '(', ')' and ':'

        Returns:
            bool: True if an operator was tokenized, False otherwise
        """
        symbol = self.code.matchany(symbols)
        if symbol is None:
            return False
        return self.addtoken('symbol', symbol)

    def tokenize_int(self):
        """
        Tokenizes an integer. There are 5 types of integer: binary, octal, decimal, hexadecimal and characters.
        This only tokenizes the integer (not the sign). If there is a minus sign, it will be tokenized as a symbol, and
        the parser will compute the negative of this value. Character integers evaluate to the ASCII value of the
        character. The value of an integer token is a CodeObject whose value attribute is the integer represented
        by the token.

        Returns:
            (bool): True if an integer was tokenized, False otherwise
        """
        if self.tokenize_bin() or self.tokenize_hex() or self.tokenize_oct() \
                or self.tokenize_dec() or self.tokenize_char():
            return True

        return False

    def tokenize_bin(self):
        """
        Tokenizes a binary integer.
        A binary integer must start with '0b' or '0B' and is followed by one or more '0's or '1's

        Returns:
            (bool): True if a binary integer was tokenized, False otherwise

        Raises:
            CompilerException: If the token starts with '0b' or '0B', but contains no binary digits directly after
        """
        start = self.code.getoffset()
        if self.code.matchany(['0b', '0B']) is None:
            return False

        if self.code.match('0'):
            n = 0
        elif self.code.match('1'):
            n = 1
        else:
            raise CompilerException(CompilerException.SYNTAX, "Invalid binary literal", self.code[0])

        while True:
            if self.code.match('0'):
                n *= 2
            elif self.code.match('1'):
                n = 2 * n + 1
            else:
                return self.addtoken('integer', self.code.substring_absolute(start), n)

    def tokenize_oct(self):
        """
        Tokenizes an octal integer.
        An octal integer must start with '0' and then is followed by zero or more characters between '0' and '7'

        Returns:
            (bool): True if an octal integer was tokenized, False otherwise
        """
        start = self.code.getoffset()
        if not self.code.match('0'):
            return False

        n = 0
        while True:
            char = self.code.matchrange('0', '7')
            if char is not None:
                n = 8 * n + int(char)
            else:
                return self.addtoken('integer', self.code.substring_absolute(start), n)

    def tokenize_dec(self):
        """
        Tokenizes a decimal integer.
        A decimal integer is a sequence of one or more characters between '0' and '9'

        Returns:
            (bool): True if a decimal integer was tokenized, False otherwise
        """
        start = self.code.getoffset()
        char = self.code.matchrange('0', '9')
        if char is None:
            return False

        n = int(char)
        while True:
            char = self.code.matchrange('0', '9')
            if char is not None:
                n = 10 * n + int(char)
            else:
                return self.addtoken('integer', self.code.substring_absolute(start), n)

    def tokenize_hex(self):
        """
        Tokenizes a hexadecimal integer.
        A hexadecimal integer starts with '0x' or '0X' and then is followed by a sequence of one or more hexadecimal
        integers. A hexadecimal integer is any character between ('0' and '9'), ('a' and 'f') or ('A' and 'F')

        Returns:
            (bool): True if a hexadecimal integer was tokenized, False otherwise

        Raises:
            CompilerException: If the token starts with '0x' or '0X', but contains no hexadecimal digits directly after
        """
        start = self.code.getoffset()
        if self.code.matchany(['0x', '0X']) is None:
            return False

        try:
            n = int(self.code[0])
            self.code.advance()
        except ValueError:
            raise CompilerException(CompilerException.SYNTAX, "Invalid hex literal", self.code[0])

        while True:
            try:
                n = 16 * n + int(self.code[0])
                self.code.advance()
            except ValueError:
                return self.addtoken('integer', self.code.substring_absolute(start), n)

    def tokenize_char(self):
        """
        Tokenizes a character integer.
        A character integer is a character with an ASCII value between 32 (space) and 126 (~) (inclusive), with a single
        quotation mark before and after it (').

        Returns:
            (bool): True if a character integer was tokenized, False otherwise

        Raises:
            CompilerException:
                - If there is a single quotation mark at the start, but there is no closing quotation mark
                    in the correct place (i.e. with one character between the 2 quotation marks)
                - If the character inside the quotation marks is outside of the ASCII range 32 to 126 (inclusive)
        """
        start = self.code.getoffset()
        if not self.code.match("'"):
            return False

        if self.code[1] != "'":
            if self.code[0] == "'":
                raise CompilerException(CompilerException.SYNTAX,
                                        "Invalid character literal. Cannot have empty character literals",
                                        self.code.substring_relative(-1))
            raise CompilerException(CompilerException.SYNTAX,
                                    "Invalid character literal. Character has no closing quotation mark",
                                    self.code[0], offset=1)

        c = self.code[0].text
        self.code.advance(2)
        if 32 <= ord(c) <= 126:
            return self.addtoken('integer', self.code.substring_absolute(start), ord(c))
        else:
            raise CompilerException(CompilerException.SYNTAX,
                                    "Invalid character literal. Only characters with an ASCII value between 32 and 126 "
                                    "(inclusive) are allowed", self.code[-2])


def tokenize(file):
    """
    Tokenizes an assembly file and returns the tokens. Takes the raw text from the assembly file as an open file object,
    and generates a 2 dimensional list of tokens. The tokens list is structured so that each line in the code is
    in a seperate row of the 2 dimensional list. Each row contains a series of tokens, stored as tuples. The first
    element of the tokens is the type of the token, stored as a string, and the second element is the value.

    There are 5 types of token: 'keyword', 'identifier', 'register', 'label', 'integer'

    More information about what constututes each type of token can be found in the documentation for the functions
    that tokenize them (e.g. Tokenizer.tokenize_label()).

    The value of the token is stored as a CodeObject. This CodeObject stores both the value of the token, and the
    original text that created the token as a PositionedString. This means that if an error is created, we can determine
    exactly where that token was in the code.

    Args:
        file (TextIOWrapper): An open file of the file to be tokenized. Must be in the mode 'r'.

    Returns:
        (list<list<tuple>>): A two dimensional list containing the tokens on each line. Each token is stored
            in a tuple containing the type of the token as a string, and the value of the token as a CodeObject
    """
    code = file.read()
    error.code = code.splitlines()
    CompilerException.file_name = os.path.realpath(file.name)
    return Tokenizer(code).tokens
