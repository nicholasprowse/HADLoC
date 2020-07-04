from error import CompilerException


def write_code(instructions, file_name):
    """
    Converts the provided list of assembly instructions, generated by a parser, into the machine code. This is then
    written to 3 different files in different formats. The first is a binary file containing the raw bytes of the
    machine code. The other two are both text files, containing the machine code in binary text and hexadecimal format.
    The name of the file to write the data to should be provided with no extension. If the file name of 'name' is
    provided, then the three files will be named 'name.bin', 'name_hex.txt' and 'name_bin.txt'. The names of these three
    files are returned from the function in a list in this same order

    Raises:
        CompilerException: If any of the provided instructions are invalid

    Args:
        instructions (list): List of instructions, generated by the parser, to be converted into machine code
        file_name (str): The file name (without the extension) to write the machine code to

    Returns:
        The names of the 3 files created, in a list, where name of the raw binary file will always be the first element
        in the list.
    """
    machinecode = [0] * len(instructions)
    for i in range(len(instructions)):
        machinecode[i] = instruction_value(instructions[i])

    files = [file_name + '.bin', file_name + '_hex.txt', file_name + '_bin.txt']
    file = open(files[0], 'wb')
    file.write(bytes(machinecode))
    file.close()

    file = open(files[1], 'w')
    for address in range(0, len(machinecode), 16):
        if address % 512 == 0:
            file.write('\u2501' * 5 + ('\u254B' if address > 0 else '\u2533') + '\u2501' * 49 + '\n     \u2503 ')
            for n in range(16):
                if n == 8:
                    file.write(" ")
                file.write("X{:1X} ".format(n))
            file.write('\n' + '\u2501' * 5 + '\u254B' + '\u2501' * 49 + '\n')
        file.write("{:03X}X \u2503 ".format(address // 16))
        for n in range(min(16, len(machinecode) - address)):
            if n == 8:
                file.write(" ")
            file.write("{:02X} ".format(machinecode[address + n]))
        file.write('\n')
    file.close()

    file = open(files[2], 'w')
    for byte in machinecode:
        file.write("{:08b}\n".format(byte))
    file.close()
    return files


# Lookup tables for various binary values used in the machine code instructions
registers = {'X': 0x00, 'L': 0x01, 'I': 0x02, 'H': 0x02, 'M': 0x03, 'Y': 0x03}
gt = 0x09
lt = 0x0C
eq = 0x0A
jmp = 0x10
# These are the instructions that have no arguments, so they always compile into the same machine code
fixed = {'jmp': jmp | lt | eq | gt, 'jlt': jmp | lt, 'jeq': jmp | eq, 'jgt': jmp | gt, 'jle': jmp | lt | eq,
         'jge': jmp | eq | gt, 'jne': jmp | lt | gt, 'nop': 0x01, 'jcs': jmp | 0x02, 'jis': jmp | 0x04, 'hlt': 0x00,
         'ics': 0x03, 'icc': 0x02}
# Arithmetic/logic instructions
unary = {'X': {'not': 0x0, 'neg': 0x8, 'inc': 0xC, 'dec': 0x4},
         'LM': {'not': 0x3, 'neg': 0xF, 'inc': 0xB, 'dec': 0x7}}
binary = {'and': 0xA, 'or': 0xE, 'add': 0x9}
arith = ['add', 'sub', 'or', 'and', 'not', 'neg', 'inc', 'dec']


def instruction_value(instruction):
    """
    Determines the 8 bit machine code value of the given instruction. The instruction argument should be a list of
    PositionObjects of the tokens in the instruction. These are generated by the parser.

    Raises:
        CompilerException: If the register arguments to the instruction are invalid

    Args:
        instruction (list): The instruction to determine the machine code value of

    Returns:
         The machine code value of the instruction. This will be an 8 bit integer
    """
    command = instruction[0]
    if command in fixed:
        return fixed[command]

    if command == 'ldb':
        return 0x80 | instruction[1]

    if command == 'mov':
        src, dst = instruction[1], instruction[2]
        if dst == 'I':
            raise CompilerException('Argument', "Cannot move into the 'I' register. The 'I' register is read only",
                                    instruction[2])

        if src == 'H':
            raise CompilerException('Argument', "Cannot move out of the 'H' register. The 'H' register write only",
                                    instruction[1])

        s = 0
        if dst == 'M':
            if src == 'M':
                return fixed['nop']
            s = 1
        if src == 'Y':
            if dst == 'Y':
                return fixed['nop']
            s = 1

        return 0x20 | s << 4 | (registers[dst] << 2) | registers[src]

    if command in ['opd', 'opi']:
        if instruction[1] in ['Y' or 'H']:
            raise CompilerException('Argument', "The '{}' register cannot be used as the argument to the '{}' "
                                                "instruction".format(instruction[1], command), instruction[1])
        d = 1 if command == 'opd' else 0
        return 0x08 | d << 2 | registers[instruction[1]]

    arithmetic = arithmetic_value(instruction)
    if arithmetic is not None:
        return arithmetic

    # In theory this is never reached, as all invalid instructions should have been caught in the tokenizing or
    # parsing stage
    raise CompilerException("Encoding", 'Instruction not encoded: ' + str(instruction), instruction[0])


def arithmetic_value(instruction):
    """
    Deterimines the machine code value of an arithmetic or logic instruction. Returns this value if the instruction
    is an arithmetic/logic command. If not, then None is returned.

    Raises:
        CompilerException: If the register arguments to the instruction are invalid
    Args:
        instruction (list): The instruction to determine the value of

    Returns:
        The machine code value of this instruction if it is an arithmetic/logic instruction. Otherwise None
    """
    if instruction[0] not in arith:
        return None

    dst, arg1 = instruction[1], instruction[2]
    if dst not in ['X', 'L']:
        raise CompilerException('Argument', "The destination register of arithmetic and logic instructions must be "
                                            "'X' or 'L'", dst)

    if arg1 in ['I', 'Y', 'H']:
        raise CompilerException('Argument', "The '{}' register cannot be used as an argument for the arithmetic and"
                                            "logic instructions".format(arg1), arg1)

    x = 1 if dst == 'X' else 0
    m = 1 if arg1 == 'M' else 0
    if instruction[0] in unary['X']:
        opcode = unary['X'][instruction[0]] if arg1 == 'X' else unary['LM'][instruction[0]]
        return 0x40 | x << 5 | m << 4 | opcode

    arg2 = instruction[3]
    if arg2 in ['I', 'Y', 'H']:
        raise CompilerException('Argument', "The '{}' register cannot be used as an argument for the arithmetic and"
                                            "logic instructions".format(arg2), arg2)
    if arg2 == 'M':
        m = 1

    if arg1 == arg2 == 'X':
        raise CompilerException('Argument', "'X' cannot be both arguments in arithmetic and logic instructions", arg2)

    if arg1 != 'X' and arg2 != 'X':
        raise CompilerException('Argument', "Arithmetic and logic instructions must have at least one argument be 'X'",
                                arg1)

    if instruction[0] == 'sub':
        opcode = 0xD if arg1 == 'X' else 0x5
    else:
        opcode = binary[instruction[0]]

    return 0x40 | x << 5 | m << 4 | opcode