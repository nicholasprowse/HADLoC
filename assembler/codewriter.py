import writer


def write_code(instructions: list[list[str | int]], file_name: str):
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
        instructions: List of instructions, generated by the parser, to be converted into machine code
        file_name: The file name (without the extension) to write the machine code to

    Returns:
        The names of the 3 files created, in a list, where name of the raw binary file will always be the first element
        in the list.
    """
    machine_code = [0] * len(instructions)
    for i in range(len(instructions)):
        machine_code[i] = instruction_value(instructions[i])

    files = [file_name + '.bin', file_name + '_hex.txt', file_name + '_bin.txt']
    file = open(files[0], 'wb')
    file.write(bytes(machine_code))
    file.close()

    file = open(files[1], 'w')
    writer.display(file, machine_code, 'hex')
    file = open(files[2], 'w')
    writer.display(file, machine_code, 'bin')

    return files


# Lookup tables for various binary values used in the machine code instructions
REGISTERS = {'X': 0x00, 'L': 0x01, 'I': 0x02, 'H': 0x02, 'M': 0x03, 'Y': 0x03}
GT = 0x09
LT = 0x0C
EQ = 0x0A
JMP = 0x10
# These are the instructions that have no arguments, so they always compile into the same machine code
FIXED = {'jmp': JMP | LT | EQ | GT, 'jlt': JMP | LT, 'jeq': JMP | EQ, 'jgt': JMP | GT, 'jle': JMP | LT | EQ,
         'jge': JMP | EQ | GT, 'jne': JMP | LT | GT, 'nop': 0x01, 'jcs': JMP | 0x02, 'jis': JMP | 0x04, 'hlt': 0x00,
         'ics': 0x03, 'icc': 0x02}
# Arithmetic/logic instructions
UNARY = {'X': {'not': 0x0, 'neg': 0x8, 'inc': 0xC, 'dec': 0x4},
         'LM': {'not': 0x3, 'neg': 0xF, 'inc': 0xB, 'dec': 0x7}}
BINARY = {'and': 0xA, 'or': 0xE, 'add': 0x9}
ARITHMETIC = ['add', 'sub', 'or', 'and', 'not', 'neg', 'inc', 'dec']


def instruction_value(instruction: list[str | int]):
    """
    Determines the 8 bit machine code value of the given instruction. The instruction argument should be a list of
    CodeObjects, str and int objects of the tokens in the instruction. These are generated by the parser.

    Raises:
        CompilerException: If the register arguments to the instruction are invalid

    Args:
        instruction (list): The instruction to determine the machine code value of

    Returns:
         The machine code value of the instruction. This will be an 8-bit integer
    """
    command = instruction[0]
    if command in FIXED:
        return FIXED[command]

    if command == 'ldb':
        return instruction[1] | 0x80

    if command == 'mov':
        src, dst = instruction[1], instruction[2]
        if dst == src:
            return FIXED['nop']

        s = int(dst == 'M' or src == 'Y')
        return 0x20 | s << 4 | REGISTERS[dst] << 2 | REGISTERS[src]

    if command in ['opd', 'opi']:
        d = 1 if command == 'opd' else 0
        return 0x08 | d << 2 | REGISTERS[instruction[1]]

    arithmetic = arithmetic_value(instruction)
    if arithmetic is not None:
        return arithmetic

    # In theory this is never reached, as all invalid instructions should have been caught in the tokenizing,
    # parsing and code writing stage
    raise Exception("This instruction {} was not able to be encoded, and no error could be found in it. Please"
                    " update the assembler to handle this instruction".format(instruction))


def arithmetic_value(instruction):
    """
    Determines the machine code value of an arithmetic or logic instruction. Returns this value if the instruction
    is an arithmetic/logic command. If not, then None is returned.

    Raises:
        CompilerException: If the register arguments to the instruction are invalid
    Args:
        instruction (list): The instruction to determine the value of

    Returns:
        The machine code value of this instruction if it is an arithmetic/logic instruction. Otherwise None
    """
    if instruction[0] not in ARITHMETIC:
        return None

    dst, arg1 = instruction[1], instruction[2]

    x = int(dst == 'X')
    m = int(arg1 == 'M')
    if instruction[0] in UNARY['X']:
        opcode = UNARY['X'][instruction[0]] if arg1 == 'X' else UNARY['LM'][instruction[0]]
        return 0x40 | x << 5 | m << 4 | opcode

    arg2 = instruction[3]
    m = int(arg1 == 'M' or arg2 == 'M')

    if instruction[0] == 'sub':
        opcode = 0xD if arg1 == 'X' else 0x5
    else:
        opcode = BINARY[instruction[0]]

    return 0x40 | x << 5 | m << 4 | opcode
