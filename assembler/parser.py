from error import CompilerException
from cstring import CodeObject

inst_formats = {'mov': ['register', 'register'], 'opd': ['register'], 'jmp': [], 'jgt': [], 'jeq': [], 'jlt': [],
                'jge': [], 'jle': [], 'jne': [], 'jcs': [], 'jis': [], 'opi': ['register'], 'hlt': [],
                'not': ['register', 'register'], 'neg': ['register', 'register'], 'inc': ['register', 'register'],
                'dec': ['register', 'register'], 'sub': ['register', 'register', 'register'],
                'and': ['register', 'register', 'register'], 'or': ['register', 'register', 'register'],
                'add': ['register', 'register', 'register'], 'nop': [], 'ics': [], 'icc': []}


class Parser:
    """
    The parser interprets each line of tokens, and converts them into instructions.

    The parser will convert the lda and ldb pseudoinstructions into the corresponding assembly instructions.
    However, if a label is used as an argument for a load instruction, it will be left as a label, as the values of
    the labels need to be determined in the labelencoder. Thus, after parsing some of the load instructions are still
    pseudoinstructions. Again, this will be resolved in the labelencoder.

    The parser will also create a dictionary of all the labels and constants present in the code. The dictionary uses
    the label as a key, and the line number as the value. Note that this line number is not final, becuase as described
    above, not all pseudoinstructions are evaluated at this stage. It will also check that no labels are used that are
    not defined in the code.

    The final function performed by the parser is confirming that each instruction has the correct number and type of
    arguments. Note: this just means that the token type of the arguments are corrent. It does not mean that the
    arguments are valid. For example, the instruction 'add H L X' would be determined to be valid at this stage,
    despite the fact that H cannot be used as the destination in arithmetic instructions. This is becuase the parser
    just checks if the type of the token is correct, but does not check the value of the token.

    The parser will generate a list of instructions. Each instruction is a list of strings or integer values. Where the
    instruction is was not generated from a pseudoinstruction, these are stored as CodeObjects. However, if the
    instructions are generated from a pseudoinstruction, primitive strings and integers are used. This is becuase, we
    can garantee these instructions will not create an error, because they are generated by the parser.

    Args:
        tokens (list<list<tuple>>): A two dimensional list containing the tokens on each line of the assembly file.
            Each token is stored in a tuple containing the type of the token as a string, and the value of the token
            as a CodeObject. This should be created using tokenizer.tokenize(text)
        warnings (list<str>): A list of warnings to display when compilation is completed. If the parser finds any
            warnings, it adds a message to this list, and it will be displayed by the assembler when assembly is
            completed

    Attributes:
        tokens (list<list<tuple>>): Stores the tokens passed in as an argument
        line (int): The line of the current instruction being parsed
        index (int): The index within the current line of the current token being parsed
        labels (dict<label, line>): A dictionary containing the labels as keys, and the line number of the label as
            the value. The line number is the line number of the instructions generated from parsing (not the final
            line number)
        constants (dict<name, value>): A dictionary containing the names of the constants as keys, and the values of
            the constants as the value. Unlike the labels dictionary, these values are final.
        instructions (list<list>): List of lists, where each list represents one instruction. Each instruction contains
            the strings and integer values required to represent the instruction.
        used_labels (list<CodeObject>): List of the labels used in the code. These are the labels that are used in load
            instructions, NOT the labels that are created. If there is an label in this list, that is not in the
            labels dictionary, then there is a CompilerException, an undefined label was used.
        used_constants (list<CodeObject>): List of the names of the constants used in the code. These are the constants
            that are used in load instructions, NOT the constants that are defined in definitions. If there is an name
            in this list, that is not in the constants dictionary, then there is a CompilerException, an undefined name
            was used

    Raises:
        CompilerException:
            - If an identifier was used that is not defined elsewhere in the code
            - The same identifier is defined twice
            - An instruction is used with the wrong amount or type of arguments
            - An integer outside of the valid range is used in a load instruction
            - If any unexpected tokens are encountered
    """

    def __init__(self, tokens, warnings):
        self.tokens = tokens
        self.line = 0
        self.index = 0
        self.labels = {}
        self.constants = {}
        self.instructions = [['nop'], ['nop']]
        self.used_labels = []
        self.used_constants = []

        self.parse_program()

        # Check that all labels are defined
        for label in self.used_labels:
            if label not in self.labels:
                raise CompilerException(
                    CompilerException.NAME, "The identifier '{}' has not been defined".format(label), label)

        # Check if there are any labels or definitions that weren't used
        for label in self.labels:
            if label not in self.used_labels:
                warnings.append(f"The label '{label}' on line {label.line()+1} was never used")

        for definition in self.constants:
            if definition not in self.used_constants:
                warnings.append(f"The constant '{definition}' on line {definition.line()+1} was never used")

        self.instructions.append(['hlt'])

    def type(self, offset=0):
        """
        Returns the type of the token offset by a given amount from the token currently being parsed.
        If the given offset is not on the same line, then an empty string is returned

        Args:
            offset (int): the offset from the current token

        Returns:
             (str) the type of the token offset by a given amount from the token currently being parsed, or an
             empty string if the given offset is not on the same line
        """
        if self.index + offset >= len(self.tokens[self.line]):
            return ''
        return self.tokens[self.line][self.index + offset][0]

    def value(self, offset=0):
        """
        Returns the value of the token offset by a given amount from the token currently being parsed.
        If the given offset is not on the same line, then None is returned

        Args:
            offset (int): the offset from the current token

        Returns:
             (CodeObject) the value of the token offset by a given amount from the token currently being parsed, or
             None if the given offset is not on the same line
        """
        if self.index + offset >= len(self.tokens[self.line]):
            return None
        return self.tokens[self.line][self.index + offset][1]

    def addinstr(self, instr):
        """
        Helper function to add a new instruction at the same time as returning True

        Args:
            instr (list): The instruction to be added. A list of CodeObjects

        Returns:
            (bool): True
        """
        self.instructions.append(instr)
        return True

    def parse_program(self):
        """
        Parses the entire list of tokens.
        Creates the labels dictionary and the used_labels list.
        Creates the instruction list and verifies the structure of the instructions are correct.
        See documentation for Parser for more information on what parsing a program achieves.

        Raises:
            CompilerException:
                - If a label was used that is not defined elsewhere in the code
                - The same label is defined twice
                - An instruction is used with the wrong amount or type of arguments
                - An integer outside of the valid range is used in a load instruction
                - If any unexpected tokens are encountered (this happens if there is an unparsed token on a line
                    after an instructions has already been parsed)
        """
        while True:
            # Each line optionally has one label or one instruction
            if not self.parse_definition():
                self.parse_label()
                self.parse_instruction()

            # After these have been parsed, there must be a new line, or the end of the file
            if self.index >= len(self.tokens[self.line]):
                self.line += 1
                self.index = 0
                # check if we've finished
                if self.line == len(self.tokens):
                    return
            else:
                # if there is not a new line, there is an unexpected token
                raise CompilerException(CompilerException.SYNTAX, 'Unexpected Token', self.value())

    def parse_label(self):
        """
        Parses a label. A label consists of an identifier token, followed by a label token.
        If the label is succesfully parsed, index is advanced past the label, and True is returned.
        The current line number is added to the labels dictionary with the key given by the value of the identifier
        token. No instructions are generated from parsing a label. If the label already exists in the labels dictionary
        a CompilerException is raised. If parsing is unsuccesful then False is returned and index is not changed.

        Returns:
            True if a label was parsed, False otherwise

        Raises:
            CompilerException: If parsing the label succeeds, but the identifier is defined elsewhere
        """
        if self.type() == 'identifier' and self.value(1) == ':':
            if self.value() in self.labels or self.value() in self.constants:
                raise CompilerException(CompilerException.NAME, f"The identifier '{self.value()}' has multiple "
                                                                f"definitions", self.value())
            self.labels[self.value()] = len(self.instructions)
            self.index += 2
            return True
        return False

    def parse_definition(self):
        """
        Parses a definition. A definition is the keyword 'define' followed by an identifier, then an integer.

        Returns:
            True if a definition was parsed, False otherwise

        Raise:
            CompilerException: If parsing the definition succeeds, but the identifier is defined elsewhere
        """
        if not (self.type() == 'keyword' and self.value() == 'define'):
            return False

        if not self.type(1) == 'identifier':
            raise CompilerException(CompilerException.ARG,
                                    "Expected identifier after a 'define' keyword", self.value(1))

        name = self.value(1)
        if name in self.labels or name in self.constants:
            raise CompilerException(CompilerException.NAME, f"The identifier '{name}' has multiple "
                                                            f"definitions", name)
        self.index += 2
        try:
            tokentype, value = self.parse_constant_expression()
        except CompilerException as ce:
            ce.msg = ce.msg.format('define')
            raise ce

        if value is None:
            raise CompilerException(CompilerException.SYNTAX, "Expected constant expression as argument to the"
                                                              " 'define' instruction", self.value())

        self.constants[name] = value
        return True

    def parse_constant_expression(self):
        """
        Parses a constant value. A constant is defined as
        ConstantExpression:
            label
            BitwiseOrExpression

        BitwiseOrExpression:
            BitwiseAndExpression ('|' BitwiseAndExpression)*

        BitwiseAndExpression:
            ArithmeticExpression ('&' ArithmeticExpression)*

        ArithmeticExpression:
            UnaryExpression (('+' | '-') UnaryExpression)*

        UnaryExpression:
            ('-' | '!')* Primary

        Primary:
            definition
            integer
            (BitwiseOrExpression)

        This allows in bitwise and arithmetic operations to bw performed on definitions and integers, where unary
        operators have the highest precedence followed by (+, -) then &, then |. This grammar prohibits operators from
        being used on labels. If a constant expression is not a label, it will be able to be evaluated completely, since
        all definitions must be defined before they are used.

        Each non-terminal above will be implemented in its own function, which returns true if it was successfully
        parsed. If a function returns False, it must restore the index back to its original value if its been changed

        Returns:
            (tokentype, value): tokentype is the type of the expression. If it is a label, then type='identifier',
                otherwise type='integer'. value is the value of the expression. This is returned as a CodeObject, which
                either contains an integer, or a string, if there was a label.
        """
        if self.type() == 'identifier' and self.value() not in self.constants:
            self.used_labels.append(self.value())
            self.index += 1
            return self.type(-1), self.value(-1)
        return 'integer', self.parse_or_expression()

    def parse_or_expression(self):
        """See docstring for parse_constant_expression"""
        value = self.parse_and_expression()
        while self.value() == '|':
            value.text += self.value().text
            self.index += 1
            value |= self.parse_and_expression()
        return value

    def parse_and_expression(self):
        """See docstring for parse_constant_expression"""
        value = self.parse_arithmetic_expression()
        while self.value() == '&':
            value.text += self.value().text
            self.index += 1
            value &= self.parse_arithmetic_expression()
        return value

    def parse_arithmetic_expression(self):
        """See docstring for parse_constant_expression"""
        value = self.parse_unary_expression()
        tokenvalue = self.value()
        while tokenvalue in ['+', '-']:
            self.index += 1
            value.text += tokenvalue.text
            if tokenvalue == '+':
                value += self.parse_unary_expression()
            elif tokenvalue == '-':
                value -= self.parse_unary_expression()
            tokenvalue = self.value()
        return value

    def parse_unary_expression(self):
        """See docstring for parse_constant_expression"""
        minus = False
        invert = False
        while self.value() in ['-', '!']:
            if self.value() == '-':
                minus = not minus
            elif self.value() == '!':
                invert = not invert
            self.index += 1
        value = self.parse_primary()
        if minus:
            value = -value
        if invert:
            value = ~value
        return value

    def parse_primary(self):
        """See docstring for parse_constant_expression"""
        value = self.value()
        if self.type() == 'identifier':
            if value in self.constants:
                self.index += 1
                self.used_constants.append(value)
                return CodeObject(self.constants[value].value, value.text)
            raise CompilerException(CompilerException.NAME,
                                    "Invalid name, '{}', used in expression. Constants must be defined before they are "
                                    "used, and labels cannot be used in expressions".format(value), value)

        if self.type() == 'integer':
            if not -32768 <= value < 65536:
                raise CompilerException(CompilerException.VALUE, "Integer literals must be in the range -32768 to 65535"
                                                                 " (inclusive)", value)
            self.index += 1
            return value

        if value == '(':
            self.index += 1
            expression_value = self.parse_or_expression()
            expression_value.text = value.text + expression_value.text
            if self.value() == ')':
                expression_value.text += self.value().text
                self.index += 1
                return expression_value
            if self.value() is None:
                raise CompilerException(CompilerException.SYNTAX, 'Unmatched bracket', value)
            else:
                raise CompilerException(CompilerException.SYNTAX, 'Invalid Syntax. Expected closing bracket',
                                        self.value())

        if value is None:
            raise CompilerException(CompilerException.SYNTAX,
                                    "Missing value for '{}' instruction. Expected label, constant, or expression "
                                    "involving constants", self.value(-1))
        else:
            raise CompilerException(CompilerException.SYNTAX,
                                    "Unexpected token. Expected label, constant, or expression involving constants",
                                    value)

    def parse_instruction(self):
        """
        Parses a single instruction. In this case an instruction refers to any line that produces machine code.
        Thus, this will parse everything except labels and definitions. Any tokens successfully parsed will be
        advanced over.

        Returns:
            True if an instruction was successfully parsed, False otherwise

        Raises:
            CompilerException:
                - An instruction is used with the wrong amount or type of arguments
                - An integer outside of the valid range is used in a load instruction
        """
        if self.type() != 'keyword':
            return False

        if self.value() in inst_formats:
            instruction = [self.value()]
            arguments = inst_formats[self.value()]

            for i in range(len(arguments)):
                if self.type(i + 1) != arguments[i]:
                    # If the argument exists, but is wrong, the error points to the wrong argument
                    # But of the argument doesn't exist, the pos of the previous argument is incremented by 2
                    # so the error will point to the poisition where the missing argument should be
                    if self.value(i + 1) is None:
                        raise CompilerException(CompilerException.ARG,
                                                "Expected {0} for argument {1} in '{2}' instruction"
                                                .format(arguments[i], i + 1, self.value()), self.value(i))
                    raise CompilerException(CompilerException.ARG, "Expected {0} for argument {1} in '{2}' instruction"
                                            .format(arguments[i], i + 1, self.value()), self.value(i + 1))

                instruction.append(self.value(i + 1))

            self.index += len(arguments) + 1
            return self.addinstr(instruction)

        # write the pseudoinstructions ldb, ldu and lda
        instr = self.value()
        if instr in ['ldb', 'ldu']:
            self.index += 1
            try:
                tokentype, value = self.parse_constant_expression()
            except CompilerException as ce:
                ce.msg = ce.msg.format(instr)
                raise ce
            self.write_load(instr, tokentype, value)
            return True

        if instr == 'lda':
            self.index += 1
            self.write_lda()
            return True

        return False

    def write_load(self, instr, tokentype, value, index=None):
        """
        Writes a load instruction using the value as the argument. The type and value arguments should be taken
        directly from the type and value fields in the token that represents the argument to this load instruction.
        The argument must be either an identifier or an integer, otherwise a CompilerException will be raised.
        Integer arguments can be up to 16 bits, but only the upper or lower 8 bits will be used, depending on the
        value of instr. The instr argument is a string and can be either 'ldu', to load the upper byte, or 'ldb' to
        load the lower byte of the argument. By default the instruction is written to the end of teh instructions
        list, however, if the index argument is included, then the load instruction is written to the location in the
        instructions list specified by index. This is so that identifier loads can be replaced when their values are
        resolved.

        If the argument is an identifier and is in the definitions dictionary, then the value stored in the dictionary
        will be used as the argument. If the argument is an identifier, but is not in the definitions dictionary, then
        the identifier will be left as the argument.

        If the argument is an integer (or defined identifier) and the eighth bit is a 0, then this will write
            ldb arg       or      ldu arg

        If the argument is an integer (or defined identifier) and the eighth bit is a 1, then this will write
            ldb !arg      or      ldu !arg
            not L L               not L L
        Where !arg is the 1's complement negation of the argument

        Warning: This function will not advance past the token it uses as the argument (due to the way it is used in
        parse_lda).
        Args:
            instr (str or CodeObject): string indicating the type of the load instruction. Can be either 'ldu' for load
                upper byte, or 'ldb' for load lower byte
            tokentype (str): The type of the argument. For a valid load instruction to be written, this should be equal
            to 'integer' or 'identifier'. Otherwise a CompilerException will be raised
            value (int or CodeObject): the value of the argument. For a valid load instruction to be written, this
                should be an int or a CodeObject containing either an int or string. Otherwise a CompilerException
                will be raised
            index: The index in the instructions list to write the load instruction to. This argument is optional, and
                if it is not included the instructions will be written to the end of the list

        Returns:
            The number of instructions written. Will be either 1 or 2, depending on the value of the argument

        Raises:
            BaseException: If tokentype is not 'integer' or 'identifier'
        """
        # If index is not supplied, set it to the end of the instructions list
        if index is None:
            index = len(self.instructions)

        if tokentype == 'identifier':
            # If the argument is an identifier, it must be a label. Since we don't yet know the values of the labels we
            # just write the load with the label as the argument. It will be rewritten when the labels are resolved in
            # the labelencoder
            self.instructions.insert(index, [instr, value])
            return 1

        if tokentype == 'integer':
            # select the upper or lower 8 bits depending on the value of instr
            value = value & 0xFF if instr == 'ldb' else (value >> 8) & 0xFF

            # if the eighth bit is zero, simple ldb instruction will work
            if 0 <= value <= 127:
                self.instructions.insert(index, ['ldb', value])
                return 1

            # Otherwise we have to load the 1's complement of the argument and the invert it
            # Note: we are inserting the instructions backwards, becuase index is not incremented between the two
            # inserts. i.e. 'not L L' will be added to the end of the list, then the 'ldb' instruction will be inserted
            # before it
            self.instructions.insert(index, ['not', 'L', 'L'])
            self.instructions.insert(index, [instr, ~value & 0xFF])
            return 2

        # We shouldn't ever reach this stage, becuase parse_constant_expression should have caught any errors
        raise BaseException("An argument that is neither an integer or label was passed into the write_load function."
                            "Occurred while parsing the instruction {} on line {}. Please update this function to "
                            "handle this case.".format(self.tokens[self.line], self.line))

    def write_lda(self):
        """
        Writes an 'lda' instruction, using the current token as the argument. 'lda' instructions compile into

            ldb arg
            mov L H
            ldu arg

        Then, the 'ldb' instructions are further compiled using the Parser.parse_load() function.

        Raises:
            CompilerException:
                - If the instruction is an 'lda' but the argument is not a identifier or integer
                - If the argument to the load instruction is an integer but it is not in the
                    range -32768 to 65536 (inclusive)
        """
        try:
            tokentype, value = self.parse_constant_expression()
            self.write_load('ldu', tokentype, value)
            self.addinstr(['mov', 'L', 'H'])
            self.write_load('ldb', tokentype, value)
        except CompilerException as ce:
            # The error needs to be caught and raised again, so we can change the message to read lda rather than ldu
            ce.msg = ce.msg.format('lda')
            raise ce
