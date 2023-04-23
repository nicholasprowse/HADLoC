import os
from hadloc import error
from enum import Enum

from hadloc.error import CompilerException
from hadloc.text_utils import PositionedString, CodeObject, Code

keywords = ['public', 'private', 'class', 'static', 'byte', 'char', 'bool', 'constructor', 'true', 'false', 'null',
            'import', 'void', 'new']

operators = ['->', '+', '-', '*', '/', '?', ':', '<<', '=', '==', '!=', '-=', '+=', '*=', '/=', '%', '%=', '!',
             '&', '|', '&=', '|=', '<', '>', '<=', '>=', '^']

separators = ['...', '(', ')', '{', '}', '[', ']', '.', ',', ';']


class Token(Enum):
    """Class to contain all the token types that can be used"""
    identifier = 0
    keyword = 1
    operator = 2
    separator = 3
    string = 4
    character = 5
    integer = 6
    float = 7


class Tokenizer:
    """
    Tokenizes a J code file. Takes the raw text from the J code file as a string, and generates a
    list of tokens, stored in the variable tokens. The tokens list contains a series of tokens, stored as tuples.
    The first element of the tokens is the type of the token, stored as a string, and the second element is the value.

    There are 5 types of token: 'keyword', 'identifier', 'literal', 'seperator', 'operator'

    More information about what constitutes each type of token can be fould in the documentation for the functions
    that tokenize them (e.g. Tokenizer.tokenize_literal()).

    The value of the token is stored as a CodeObject. This CodeObject stores both the value of the token, and the
    original text that created the token as a PositionedString. This means that if an error is created, we can determine
    exactly where that token was in the code.

    Args:
        text (str): the raw text to be tokenized, obtained from the J code file, stored as a string

    Attributes:
        code (Code): The code that is being tokenized. This object stored the current location within the text
            that is currently being tokenized.
        tokens (list<list<tuple>>): A list containing the tokens from the text. Each token is stored
            in a tuple containing the type of the token as a string, and the value of the token as a CodeObject

    Raises:
        CompilerException: If there is a syntax error in the J code, a Compiler exception will be raised
            containing the location and cause of the error
    """

    def __init__(self, text):
        # Add new line at end as is simplifies single line comment checking
        self.code = Code(text + '\n')
        # tokens = (type, value)
        self.tokens = []

        # The code should be a series of alternating tokens and whitespace/comment sections. As such, we start by
        # advancing past any whitespace/comments at the start, before continouosly tokenizing a token, and advancing
        # over whitespace/comment
        self.skip_whitespace_and_comments()
        while self.code.has_more():
            if not (self.tokenize_literal() or self.tokenize_keyword() or self.tokenize_operator() or
                    self.tokenize_separator() or self.tokenize_identifier()):
                raise CompilerException(CompilerException.SYNTAX, 'Unexpected character', self.code[0])

            self.skip_whitespace_and_comments()

    def addtoken(self, tokentype, text, value=None):
        """
        Helper function to add a new token at the same time as returning True. The text and value arguments are wrapped
        in a CodeObject. If value is not provided, it will be set to the value of text.

        Args:
            tokentype (Token): The type of the token.
            text (PositionedString): The string from the code that generated the token
            value: The value of the token. This represents the value of the token. For example, if the token is an
                integer, value would be an int, that is the value of the token. If value is not passed, it gets set to
                text

        Returns:
            (bool): True
        """
        if value is None:
            value = text.text
        self.tokens.append((tokentype, CodeObject(value, text)))
        return True

    def skip_whitespace_and_comments(self):
        """
        Skips over any whitespace, and comments. Comments consist of any text between the '/*' and '*/' tokens, or
        any text after the '//' token but before the end of the line
        """
        should_continue = True
        while should_continue:
            should_continue = False
            while self.code[0].isspace():
                should_continue = True
                self.code.advance()

            if self.code.match('//'):
                should_continue = True
                # Move offset to end of the current line
                self.code.advance_past('\n')

            comment_start = self.code.substring(length=2, relative=True)
            if self.code.match('/*'):
                should_continue = True
                if self.code.advance_past('*/') is None:
                    raise CompilerException(error.CompilerException.SYNTAX, 'Comment not closed', comment_start)

    def tokenize_keyword(self):
        """
        Tokenizes a keyword. A keyword is any of the following words
            public, private, class, static, byte, char, boolean, constructor, true, false, null, import, void, new

        Returns:
            bool: True if a keyword was tokenized, False otherwise
        """
        word = self.code.match(*keywords)
        if word is not None:
            return self.addtoken(Token.keyword, word)
        return False

    def tokenize_identifier(self):
        """
        An identifier is any sequence of alphanumeric characters or '_' and '$'. The first character of an identifier
        cannot be a number or '$'

        Returns:
             bool: True if an identifier was tokenized, False otherwise
        """
        word = self.code[0]
        if not (word.isalpha() or word == '_'):
            return False

        for i in range(1, len(self.code)):
            if self.code[i].isalnum() or self.code[i] == '_' or self.code[i] == '$':
                word += self.code[i]
            else:
                break

        self.code.advance(len(word))
        return self.addtoken(Token.identifier, word)

    def tokenize_operator(self):
        """
        Tokenizes an operator. An operator is any one of the following
            ->, +, -, *, /, ?, :, <<, >>, =, ==, !=, -=, +=, *=, /=, %, %=, !, &, |, &=, |=, <, >, <=, >=, ^

        Returns:
            bool: True if an operator was tokenized, False otherwise
        """
        operator = self.code.match(*operators)
        if operator is not None:
            return self.addtoken(Token.operator, operator)
        return False

    def tokenize_separator(self):
        """
        Tokenizes a separator. A separator is any one of the following
            '...', '(', ')', '{', '}', '[', ']', '.', ',', ';'

        Returns:
            bool: True if an separator was tokenized, False otherwise
        """
        separator = self.code.match(*separators)
        if separator is not None:
            return self.addtoken(Token.separator, separator)
        return False

    def tokenize_literal(self):
        """
        Tokenizes a literal. There are four types of literal: floating point, integer, character and string.
        See the docstrings for the function that tokenize each of these tokens for more information on each ones
        structure

        Returns:
            bool: True if a literal was tokenized. False otherwise
        """
        return self.tokenize_float() or self.tokenize_int() or self.tokenize_char() or self.tokenize_string()

    def tokenize_float(self):
        """
        Tokenizes a floating point literal. A floating point literal is defined as
        floatliteral    ::=  (digits '.' digits? exponent?)
                           | ('.' digits exponent?)
                           | (digits exponent)
        exponent        ::=  ('e' | 'E') ('-' | '+')? digits
        digits          ::=  [0-9]*

        Returns:
            bool: True if a floating point literal is successfully tokenized, False otherwise

        Raises:
            CompilerException: If an exponent part is started with an 'e', but there are no digits after the 'e'.
                In this case, the token can't be anything but a float, but it is an invalid float
        """
        start = self.code.offset
        integerdigits = ''
        fractionaldigits = ''
        exponentdigits = ''
        exponentsign = '+'

        while self.code[0].isnumeric():
            integerdigits += self.code.advance().text

        if self.code[0] == '.':
            self.code.advance()
            while self.code[0].isnumeric():
                fractionaldigits += self.code.advance().text
            if len(integerdigits) == len(fractionaldigits) == 0:
                # There was a decimal point, but no digits so this is not a float
                self.code.offset = start
                return False
        else:
            if len(integerdigits) == 0:
                # no integer digits and no decimal point means this is not a float
                self.code.offset = start
                return False
            else:
                # There are digits, but no decimal point, so we require the exponent
                if not self.code.match('e') and not self.code.match('E'):
                    self.code.offset = start
                    return False
                if self.code.match('+'):
                    exponentsign = '+'
                elif self.code.match('-'):
                    exponentsign = '-'
                while self.code[0].isnumeric():
                    exponentdigits += self.code.advance().text
                if len(exponentdigits) == 0:
                    raise CompilerException(CompilerException.SYNTAX,
                                            'Invalid floating point literal. Missing expenential digits',
                                            self.code.substring(start=start))

        if len(exponentdigits) == 0:
            if self.code.match('e') or self.code.match('E'):
                if self.code.match('+'):
                    exponentsign = '+'
                elif self.code.match('-'):
                    exponentsign = '-'
                while self.code[0].isnumeric():
                    exponentdigits += self.code.advance().text
                if len(exponentdigits) == 0:
                    print(self.code[0])
                    raise CompilerException(CompilerException.SYNTAX,
                                            'Invalid floating point literal. Missing expenential digits',
                                            self.code.substring(start=start))
            else:
                exponentdigits = '0'

        return self.addtoken(Token.float, self.code.substring(start=start),
                             (integerdigits, fractionaldigits, exponentsign, exponentdigits))

    def tokenize_int(self):
        """
        Tokenizes an integer. There are 4 types of integer: binary, octal, decimal and hexadecimal.
        This only tokenizes the integer (not the sign). If there is a minus sign, it will be tokenized as an operator,
        and the parser will compute the negative of this value. The value of an integer token is a CodeObject whose
        value attribute is the integer represented by the token.

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
        start = self.code.offset
        if self.code.match('0b', '0B') is None:
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
                return self.addtoken(Token.integer, self.code.substring(start=start), n)

    def tokenize_oct(self):
        """
        Tokenizes an octal integer.
        An octal integer must start with '0' and then is followed by zero or more characters between '0' and '7'

        Returns:
            (bool): True if an octal integer was tokenized, False otherwise
        """
        start = self.code.offset
        if not self.code.match('0'):
            return False

        n = 0
        while True:
            char = self.code.match_range('0', '7')
            if char is not None:
                n = 8 * n + int(char)
            else:
                return self.addtoken(Token.integer, self.code.substring(start=start), n)

    def tokenize_dec(self):
        """
        Tokenizes a decimal integer.
        A decimal integer is a sequence of one or more characters between '0' and '9'

        Returns:
            (bool): True if a decimal integer was tokenized, False otherwise
        """
        start = self.code.offset
        char = self.code.match_range('0', '9')
        if char is None:
            return False

        n = int(char)
        while True:
            char = self.code.match_range('0', '9')
            if char is not None:
                n = 10 * n + int(char)
            else:
                return self.addtoken(Token.integer, self.code.substring(start=start), n)

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
        start = self.code.offset
        if self.code.match('0x', '0X') is None:
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
                return self.addtoken(Token.integer, self.code.substring(start=start), n)

    def tokenize_char(self):
        """
        Tokenizes a character. A character is defined as follows
        characterliteral    ::=  "'" (character | hexcharacter | backslashescape) "'"
        hexcharacter        ::=  "\" hexdigit hexdigit
        hexdigit            ::=  [0-9] | [a-f] | [A-F]
        backslashescape     ::=  "\\"
        character           ::=  Any character with ASCII value between 32 and 126 (inclusive)

        Returns:
            (bool): True if a character was tokenized, False otherwise

        Raises:
            CompilerException:
                - If there is a single quotation mark at the start, but there is no closing quotation mark
                    in the correct place
                - If the character inside the quotation marks is outside of the ASCII range 32 to 126 (inclusive)
                - If an invalid escape is used
        """
        start = self.code.offset
        if not self.code.match("'"):
            return False
        if self.code.match('\\'):
            if self.code.match('\\'):
                character = '\\'
            else:
                try:
                    value = int(self.code[0]) * 16 + int(self.code[1])
                    character = chr(value)
                    self.code.advance(2)
                except ValueError:
                    raise CompilerException(CompilerException.SYNTAX, 'Invalid hex escape in character literal',
                                            self.code.substring(start=-1, end=2, relative=True))
        else:
            character = self.code[0].text
            self.code.advance()
            if not 32 <= ord(character) <= 126:
                raise CompilerException(CompilerException.SYNTAX,
                                        "Invalid character. Only characters with an ASCII value between 32 (space) and "
                                        "126 (~) can be used in character literals", self.code[-1])

        if self.code.match("'"):
            return self.addtoken(Token.character, self.code.substring(start=start), character)

        if character == "'":
            raise CompilerException(CompilerException.SYNTAX,
                                    "Invalid character literal. Cannot have empty character literals",
                                    self.code.substring(start=-2, relative=True))
        raise CompilerException(CompilerException.SYNTAX,
                                "Invalid character literal. Character has no closing quotation mark",
                                self.code.substring(start=-2, relative=True))

    def tokenize_string(self):
        """
        Tokenizes a string literal. A String literal is defined as follows
        stringliteral       ::= '"' (character | hexcharacter | escape)* '"'
        hexcharacter        ::=  "\" hexdigit hexdigit
        hexdigit            ::=  [0-9] | [a-f] | [A-F]
        escape              ::=  '\\' | '\"'
        character           ::=  Any character with ASCII value between 32 and 126 (inclusive)

        Returns:
            bool: True if a string literal was tokenized, False otherwise

        Raises:
            CompilerException:
                - If there is a double quotation mark at the start, but there is no closing quotation mark on the same
                    line
                - If any characters inside the quotation marks is outside of the ASCII range 32 to 126 (inclusive)
                - If an invalid escape is used
        """
        start = self.code.offset
        string = ""
        if not self.code.match('"'):
            return False

        while self.code[0] != '"':
            if self.code.match('\\'):
                if self.code.match('\\'):
                    string += '\\'
                elif self.code.match('"'):
                    string += '"'
                else:
                    try:
                        value = int(self.code[0]) * 16 + int(self.code[1])
                        string += chr(value)
                        self.code.advance(2)
                    except ValueError:
                        raise CompilerException(CompilerException.SYNTAX, 'Invalid hex escape in character literal',
                                                self.code.substring(start=-1, end=2, relative=True))
            else:
                character = self.code.advance().text
                string += character
                if character == '\n':
                    raise CompilerException(CompilerException.SYNTAX,
                                            "Invalid string literal. String has no closing quotation mark",
                                            self.code.substring(start=start, length=1))
                if not 32 <= ord(character) <= 126:
                    raise CompilerException(CompilerException.SYNTAX,
                                            "Invalid character. Only characters with an ACSII value between 32 (space) "
                                            "and 126 (~) can be used in string literals", self.code[-1])

        self.code.advance()
        return self.addtoken(Token.string, self.code.substring(start=start), string)


def tokenize(file):
    """
    Tokenizes a J code file and returns the tokens. Takes the raw text from the J code file as a string, and generates a
    list of tokens, stored in the variable tokens. The tokens list contains a series of tokens, stored as tuples.
    The first element of the tokens is the type of the token, stored as a string, and the second element is the value.

    There are 5 types of token: 'keyword', 'identifier', 'literal', 'seperator', 'operator'

    More information about what constitutes each type of token can be fould in the documentation for the functions
    that tokenize them (e.g. Tokenizer.tokenize_literal()).

    The value of the token is stored as a CodeObject. This CodeObject stores both the value of the token, and the
    original text that created the token as a PositionedString. This means that if an error is created, we can determine
    exactly where that token was in the code.

    Args:
        file (TextIOWrapper): the file containing the raw text to be tokenized

    Returns:
        tokens (list<list<tuple>>): A list containing the tokens from the text. Each token is stored
            in a tuple containing the type of the token as a string, and the value of the token as a CodeObject

    Raises:
        CompilerException: If there is a syntax error in the J code, a Compiler exception will be raised
            containing the location and cause of the error
    """
    code = file.read()
    error.code = code.splitlines()
    CompilerException.file_name = os.path.realpath(file.name)
    return Tokenizer(code).tokens
