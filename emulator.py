import sys


def remove_display():
    print('\b'*84)


class Display:

    def __init__(self):
        self.cursor_line = 0
        self.cursor_pos = 0
        self.text = [' '*20]*4

    def print_display(self):
        for line in self.text:
            print(line)

    def data(self, val):
        self.text[self.cursor_line][self.cursor_pos] = chr(val)
        self.cursor_pos += 1
        if self.cursor_pos >= 20:
            self.cursor_line += 1
        if self.cursor_line >= 4:
            self.cursor_line = 0


class Computer:

    def __init__(self, program):
        self.L = 0
        self.H = 0
        self.PC = 0
        self.X = 0
        self.Y = 0
        self.IN = 0
        self.CF = False
        self.IF = False
        self.RAM = [0] * (2**15)
        self.ROM = program
        self.ROM += [0] * (2**15 - len(program))
        self.display = Display()

    def input(self, val):
        self.IN = val
        self.IF = True

    def print_state(self):
        pass

    def read_mem(self):
        """Gets the current memory value"""
        return self.RAM[self.H << 8 | self.L]

    def write_mem(self, value):
        """Writes the given value to the current memory location"""
        self.RAM[self.H << 8 | self.L] = value

    def execute(self):
        """Executes a single instruction"""
        instruction = self.ROM[self.PC]

        # Load byte instruction
        if instruction & 0x80:
            self.L = instruction & 0x7F
            self.PC += 1

        # Arithmetic/Logic instruction
        elif instruction & 0x40:
            self.execute_al(instruction & 0x20, instruction & 0x10, instruction & 0x0F)
            self.PC += 1

        # Move instruction
        elif instruction & 0x20:
            src = instruction & 0x03
            srcval = self.L
            s = instruction & 0x10
            if src == 1:
                srcval = self.X
            elif src == 2:
                srcval = self.IN
            elif src == 3 and s:
                srcval = self.Y
            elif src == 3:
                srcval = self.read_mem()

            dst = (instruction >> 2) & 0x03
            if dst == 0:
                self.L = srcval
            elif dst == 1:
                self.X = srcval
            elif dst == 2:
                self.H = srcval & 0x7F
            elif src == 3 & s:
                self.write_mem(srcval)
            elif src == 3:
                self.Y = srcval

            self.PC += 1

        # Jump instruction
        elif instruction & 0x10:
            self.PC += 1
            if instruction & 0x08:
                if instruction & 0x01 and 0 < self.X < 127:
                    self.PC = self.H << 8 | self.L
                if instruction & 0x02 and self.X == 0:
                    self.PC = self.H << 8 | self.L
                if instruction & 0x01 and self.X >= 128:
                    self.PC = self.H << 8 | self.L
            else:
                if instruction & 0x02 and self.CF:
                    self.PC = self.H << 8 | self.L
                if instruction & 0x04 and self.IF:
                    self.PC = self.H << 8 | self.L

        # Out instruction
        elif instruction & 0x08:
            self.PC += 1
            src = instruction & 0x03
            srcval = self.L
            s = instruction & 0x10
            if src == 1:
                srcval = self.X
            elif src == 2:
                srcval = self.IN
            elif src == 3 and s:
                srcval = self.Y
            elif src == 3:
                srcval = self.read_mem()

            if instruction & 0x04:
                self.display.data(srcval)

        # nop
        elif instruction & 0x40 or instruction == 1:
            self.PC += 1

        # Carry instruction
        elif instruction & 0x02:
            if self.CF and instruction == 3:
                self.H += 1
            if not self.CF and instruction == 2:
                self.H += 1
            self.H &= 0x7F
            self.PC += 1

    def execute_al(self, x, m, opcode):
        b = self.read_mem() if m else self.L
        result = 0
        if opcode == 0:
            result = ~self.X
        if opcode == 1:
            result = (~self.X) | b
        if opcode == 2:
            result = ~(self.X & b)
        if opcode == 3:
            result = ~b
        if opcode == 4:
            result = self.X - 1
            self.CF = False if self.X & 0x100 else True
        if opcode == 5:
            result = b - self.X
            self.CF = True if self.X & 0x100 else False
        if opcode == 6:
            result = ~(self.X & b)
        if opcode == 7:
            result = b - 1
            self.CF = False if self.X & 0x100 else True
        if opcode == 8:
            result = -self.X
            self.CF = False if self.X & 0x100 else True
        if opcode == 9:
            result = self.X + b
            self.CF = True if self.X & 0x100 else False
        if opcode == 10:
            result = self.X & b
        if opcode == 11:
            result = b + 1
            self.CF = False if self.X & 0x100 else True
        if opcode == 12:
            result = self.X + 1
            self.CF = False if self.X & 0x100 else True
        if opcode == 13:
            result = self.X - b
            self.CF = True if self.X & 0x100 else False
        if opcode == 14:
            result = self.X or b
        if opcode == 15:
            result = -b
            self.CF = False if self.X & 0x100 else True

        if x:
            self.X = result & 0xFF
        else:
            self.L = result & 0xFF


def main():
    file = open("/Users/nicholasprowse/Desktop/print_decimal.bin", 'rb')
    computer = Computer(list(file.read()))
    file.close()
    del file
    while computer.execute() or True:
        pass


if __name__ == '__main__':
    main()
