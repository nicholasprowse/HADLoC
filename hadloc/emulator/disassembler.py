from .word import Word


ALU_MAPPING = {
    0b0000: 'not {dst} X',
    0b0011: 'not {dst} {arg}',
    0b1000: 'neg {dst} X',
    0b1111: 'neg {dst} {arg}',
    0b1100: 'inc {dst} X',
    0b1011: 'inc {dst} {arg}',
    0b0100: 'dec {dst} X',
    0b0111: 'dec {dst} {arg}',
    0b1101: 'sub {dst} X {arg}',
    0b0101: 'sub {dst} {arg} X',
    0b1010: 'and {dst} X {arg}',
    0b1110: 'or {dst} X {arg}',
    0b1001: 'add {dst} X {arg}',
    0b0001: '',
    0b0110: 'nand {dst} X {arg}',
    0b0010: 'nand {dst} X {arg}'
}


def disassemble(instruction: Word) -> str:
    msb = instruction.msb()
    # Load byte instruction
    if msb == 7:
        val = instruction[:7]
        return f'ldb {val}'

    # Arithmetic/Logic instruction
    if msb == 6:
        destination = 'X' if instruction[5] else 'L'
        argument = 'M' if instruction[4] else 'L'
        return ALU_MAPPING[instruction[:4].val].format(dst=destination, arg=argument)

    # Move instruction
    if msb == 5:
        source = instruction[:2].val
        if source == 3:
            source += instruction[4].val
        source_name = ['X', 'L', 'I', 'M', 'Y'][source]
        destination = instruction[2:4].val
        if destination == 3:
            destination += instruction[4].val
        destination_name = ['X', 'L', 'H', 'Y', 'M'][destination]
        return f'mov {source_name} {destination_name}'

    # Jump instruction
    if msb == 4:
        opcode = instruction[:3]
        if instruction[3]:
            gt = 0x01
            eq = 0x02
            lt = 0x04
            return {lt | eq | gt: 'jmp', lt: 'jlt', eq: 'jeq', gt: 'jgt', lt | eq: 'jle',
                    eq | gt: 'jge', lt | gt: 'jne', 0x00: 'nop'}[opcode.val]
        else:
            if instruction[1] and not instruction[2]:
                return 'jcs'
            if not instruction[1] and instruction[2]:
                return 'jis'
            if instruction[1] and instruction[2]:
                return ''
            return 'nop'

    # Out instruction
    if msb == 3:
        source = instruction[:2]
        source_name = ['X', 'L', 'I', 'M'][source]
        return f'{"opd" if instruction[2] else "opi"} {source_name}'

    # No Operation instruction
    if msb in [2, 0]:
        return 'nop'

    # Carry instruction
    if msb == 1:
        return 'ics' if instruction[0] else 'icc'

    # Halt instruction
    if instruction == 0:
        return 'hlt'
    return ''
