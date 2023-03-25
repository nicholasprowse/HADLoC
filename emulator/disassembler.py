from .word import Word


def disassemble(instruction: Word) -> str:
    msb = instruction.msb()
    if msb == 7:
        val = instruction[:7]
        return f'ldb {val}'

    if msb in [2, 0]:
        return 'nop'

    if instruction == 0:
        return 'hlt'
    return ''
