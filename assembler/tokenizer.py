import os
import error

from error import CompilerException
from cstring import LinedCode, PositionObject

keywords = ['lda', 'ldb', 'ldu', 'mov', 'jmp', 'jlt', 'jeq', 'jgt', 'jle', 'jge', 'jne', 'nop', 'jis', 'jcs', 'opd',
            'opi', 'hlt', 'not', 'neg', 'inc', 'dec', 'sub', 'and', 'or', 'add', 'ics', 'icc', 'define']

registers = ['L', 'H', 'M', 'I', 'X', 'Y']


class Tokenizer:
    """
    Tokenizes an assembly file. Takes the raw text from the assembly file as a string, and generates a 2 dimensional
    list of tokens, stored in the variable tokens. The tokens list is structured so that each line in the code is
    in a seperate row of the 2 dimensional list. Each row contains a series of tokens, stored as tuples. The first
    element of the tokens is the type of the token, stored as a string, and the second element is the value.

    There are 5 types of token: 'keyword', 'identifier', 'register', 'label', 'integer'

    More information about what constututes each type of token can be fould in the documentation for the functions
    that tokenize them (e.g. Tokenizer.tokenize_label()).

    The value of the token is stored as a String object for keywords, identifiers, registers and labels. Integer
    values are stored as PositionObjects. This means that, if there is an error parsing, an error can be generated
    showing the location of the error in the original code.

    Args:
        text (str): the raw text to be tokenized, obtained from the assembly file, stored as a string

    Attributes:
        code (LinedCode): The code that is being tokenized. This object stored the current location within the text
            that is currently being tokenized.
        tokens (list<list<tuple>>): A two dimensional list containing the tokens on each line. Each token is stored
            in a tuple containing the type of the token as a string, and the value of the token as a String object or
            a PositionObject.

    Raises:
        CompilerException: If there is a syntax error in the assembly code, a Compiler exception will be raised
        containing the location and cause of the error
    """
    def __init__(self, text):
        self.code = LinedCode(text)
        # tokens = (type, value)
        self.tokens = [[]]

        # while there are more characters, move past whitespace and then attempt to create a token.
        # If a token cannot be created then there is a syntax error in the code.
        # If there is whitespace at the end of code, then this would skip past it, but not be able to generate a
        # token, creating an error when there shouldn'nt be one. However, this won't happen because leading and
        # trailing whitespace is removed in the LinedCode Object.
        while self.code.hasmore():
            self.code.skip_whitespace()

            if not (self.tokenize_int() or self.tokenize_keyword_identifier_register() or self.tokenize_label()
                    or self.newline()):
                raise CompilerException('Syntax', 'Unexpected character', self.code[0])

    def addtoken(self, tokentype, value):
        """
        Helper function to add a new token at the same time as returning True

        Args:
            tokentype (str): The type of the token.
                Must be one of 'keyword', 'identifier', 'register', 'label', 'integer'
            value: The value of the token. Should be either a String object or a PositionObject, so that line and
                position data is stored with the value

        Returns:
            (bool): True
        """
        self.tokens[-1].append((tokentype, value))
        return True

    def tokenize_label(self):
        """
        Tokenizes a label. A label is simply any instance of a colon, ':'
        The value of a label is a String object containing the colon that created the label

        Returns:
            (bool): True, if a label token was created, False otherwise.
        """
        if self.code.match(':'):
            return self.addtoken('label', ':')

    def tokenize_keyword_identifier_register(self):
        """
        Tokenizes an intance of a keyword, identifer or register. Will only tokenize one token.
        A keyword is one of:
            ('lda', 'ldb', 'mov', 'jmp', 'jlt', 'jeq', 'jgt', 'jle', 'jge', 'jne', 'nop', 'jmpc', 'jmpi', 'out',
            'outi', 'hlt', 'not', 'neg', 'inc', 'dec', 'sub', 'and', 'or', 'add', 'carry', 'define')

        A register is one of:
            ('L', 'H', 'M', 'I', 'X', 'Y')

        An identifer is any other sequence of alphanumeric characters or underscores, where the first character is
        not a numeric character.

        All three of these token types use a String object for the value

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

    def tokenize_int(self):
        """
        Tokenizes an integer. There are 5 types of integer: binary, octal, decimal, hexadecimal and characters.
        All types of integer except characters can have a negative sign, '-', before them, and the value will be the
        2's complement value.
        Character integers evaluate to the ASCII value of the character.
        The value of an integer token is a PositionObject whose value attribute is the integer represented by the token.

        Returns:
            (bool): True if an integer was tokenized, False otherwise
        """
        pos = not self.code.match('-')

        if self.tokenize_bin(pos) or self.tokenize_hex(pos) or self.tokenize_oct(pos) \
                or self.tokenize_dec(pos) or self.tokenize_char(pos):
            return True

        if not pos:
            raise CompilerException("Syntax", "Unexpected character", self.code[-1])
        else:
            return False

    def tokenize_bin(self, pos):
        """
        Tokenizes a binary integer. Will not tokenize the negative sign before it, so if there is a negative sign, this
        must already be advanced past. The pos argument is a boolean value indicating if this should be tokenized as a
        positive integer or a negative integer.
        A binary integer must start with '0b' or '0B' and is followed by one or more '0's or '1's

        Args:
            pos (bool): A boolean value indicating if this integer is positive or not. True means it is positive,
            False means its negative

        Returns:
            (bool): True if a binary integer was tokenized, False otherwise

        Raises:
            CompilerException: If the token starts with '0b' or '0B', but contains no binary digits directly after
        """
        first = self.code[0]
        if not (self.code.match('0b') or self.code.match('0B')):
            return False

        if self.code.match('0'):
            n = 0
        elif self.code.match('1'):
            n = 1
        else:
            raise CompilerException("Syntax", "Invalid binary literal", self.code[-2])

        while True:
            if self.code.match('0'):
                n *= 2
            elif self.code.match('1'):
                n = 2 * n + 1
            else:
                return self.addtoken('integer', PositionObject(n if pos else -n, first.line, first.pos))

    def tokenize_oct(self, pos):
        """
        Tokenizes an octal integer. Will not tokenize the negative sign before it, so if there is a negative sign, this
        must already be advanced past. The pos argument is a boolean value indicating if this should be tokenized as a
        positive integer or a negative integer.
        An octal integer must start with '0' and then is followed by zero or more characters between '0' and '7'

        Args:
            pos (bool): A boolean value indicating if this integer is positive or not. True means it is positive,
            False means its negative

        Returns:
            (bool): True if an octal integer was tokenized, False otherwise
        """
        first = self.code[0]
        if not self.code.match('0'):
            return False

        n = 0
        while True:
            char = self.code.matchrange('0', '7')
            if char is not None:
                n = 8 * n + int(char)
            else:
                return self.addtoken('integer', PositionObject(n if pos else -n, first.line, first.pos))

    def tokenize_dec(self, pos):
        """
        Tokenizes a decimal integer. Will not tokenize the negative sign before it, so if there is a negative sign, this
        must already be advanced past. The pos argument is a boolean value indicating if this should be tokenized as a
        positive integer or a negative integer.
        A decimal integer is a sequence of one or more characters between '0' and '9'

        Args:
            pos (bool): A boolean value indicating if this integer is positive or not. True means it is positive,
            False means its negative

        Returns:
            (bool): True if a decimal integer was tokenized, False otherwise
        """
        first = self.code[0]
        char = self.code.matchrange('0', '9')
        if char is None:
            return False

        n = int(char)
        while True:
            char = self.code.matchrange('0', '9')
            if char is not None:
                n = 10 * n + int(char)
            else:
                return self.addtoken('integer', PositionObject(n if pos else -n, first.line, first.pos))

    def tokenize_hex(self, pos):
        """
        Tokenizes a hexadecimal integer. Will not tokenize the negative sign before it, so if there is a negative sign,
        this must already be advanced past. The pos argument is a boolean value indicating if this should be tokenized
        as a positive integer or a negative integer.
        A hexadecimal integer starts with '0x' or '0X' and then is followed by a sequence of one or more hexadecimal
        integers. A hexadecimal integer is any character between ('0' and '9'), ('a' and 'f') or ('A' and 'F')

        Args:
            pos (bool): A boolean value indicating if this integer is positive or not. True means it is positive,
            False means its negative

        Returns:
            (bool): True if a hexadecimal integer was tokenized, False otherwise

        Raises:
            CompilerException: If the token starts with '0x' or '0X', but contains no hexadecimal digits directly after
        """
        first = self.code[0]
        if not (self.code.match('0x') or self.code.match('0X')):
            return False

        try:
            n = int(self.code[0])
            self.code.advance()
        except ValueError:
            raise CompilerException("Syntax", "Invalid hex literal", self.code[-2])

        while True:
            try:
                n = 16 * n + int(self.code[0])
                self.code.advance()
            except ValueError:
                return self.addtoken('integer', PositionObject(n if pos else -n, first.line, first.pos))

    def tokenize_char(self, pos):
        """
        Tokenizes a character integer. The pos parameter indicates if a negative sign (-) was before this token. Since
        character integers cannot be negative, if tokenization succeeds and pos is False, a CompilerException will be
        raised.
        A character integer is a character with an ASCII value between 32 (space) and 126 (~) (inclusive), with a single
        quotation mark before and after it (').

        Args:
            pos (bool): A boolean value indicating if there was a negative sign (-) directly before this token.
            True, indicates there was no negative sign, and False indicates there was a negative sign

        Returns:
            (bool): True if a character integer was tokenized, False otherwise

        Raises:
            CompilerException:
                - If there is a single quotation mark at the start, but there is no closing quotation mark
                    in the correct place (i.e. with one character between the 2 quotation marks)
                - If the character inside the quotation marks is outside of the ASCII range 32 to 126 (inclusive)
                - If tokenization succeeds and pos is False
        """
        if not self.code.match("'"):
            return False

        if self.code[1] != "'":
            raise CompilerException("Syntax", "Invalid character literal",
                                    self.code[0] if self.code[0] == "'" else self.code[-1])

        c = self.code[0].chars[0].value
        self.code.advance(2)
        if 32 <= ord(c) <= 126:
            if not pos:
                raise CompilerException("Syntax", "Unexpected character", self.code[-4])
            return self.addtoken('integer', PositionObject(ord(c), self.code[-2].line, self.code[-2].pos))
        else:
            raise CompilerException("Syntax", "Invalid character literal", self.code[-2])


def tokenize(file):
    """
    Tokenizes an assembly file and returns the tokens. Takes the raw text from the assembly file as an open file object,
    and generates a 2 dimensional list of tokens. The tokens list is structured so that each line in the code is
    in a seperate row of the 2 dimensional list. Each row contains a series of tokens, stored as tuples. The first
    element of the tokens is the type of the token, stored as a string, and the second element is the value.

    There are 5 types of token: 'keyword', 'identifier', 'register', 'label', 'integer'

    More information about what constututes each type of token can be found in the documentation for the functions
    that tokenize them (e.g. Tokenizer.tokenize_label()).

    The value of the token is stored as a String object for keywords, identifiers, registers and labels. Integer
    values are stored as PositionObjects. This means that, if there is an error parsing, an error can be generated
    showing the location of the error in the original code.

    Args:
        file (TextIOWrapper): An open file of the file to be tokenized. Must be in the mode 'r'.

    Returns:
        (list<list<tuple>>): A two dimensional list containing the tokens on each line. Each token is stored
            in a tuple containing the type of the token as a string, and the value of the token as a String object or
            a PositionObject.
    """
    code = file.read()
    error.code = code.splitlines()
    CompilerException.file_name = os.path.realpath(file.name)
    return Tokenizer(code).tokens


def main():
    f = open("/Users/nicholasprowse/Desktop/mult.asm")
    try:
        tokens = tokenize(f)
        for i in tokens:
            print(i)
    except CompilerException as cs:
        cs.display()
    f.close()


if __name__ == '__main__':
    main()
