import curses

from .word import Word

OPCODE_MAPPING = {
    0b0000: 0b001101,
    0b0011: 0b110001,
    0b1000: 0b001111,
    0b1111: 0b110011,
    0b1100: 0b011111,
    0b1011: 0b110111,
    0b0100: 0b001110,
    0b0111: 0b110010,
    0b1101: 0b010011,
    0b0101: 0b000111,
    0b1010: 0b000000,
    0b1110: 0b010101,
    0b1001: 0b000010,
    0b0001: 0b000101,
    0b0110: 0b000001,
    0b0010: 0b000001
}


class Display:
    def __init__(self, screen):
        self.screen = screen
        self.width = 20
        self.height = 4
        self.address = 0
        self.increment = 1
        self.text = [[' '] * self.width for _ in range(self.height)]

    def render(self):
        if self.screen is None:
            return

        for i, line in enumerate(self.text):
            # Curses throws error if cursor exceeds screen bounds. Render still works, so we just need to catch the
            # error, and everything will work
            try:
                self.screen.addstr(i, 0, ''.join(line), curses.color_pair(1))
            except curses.error:
                pass
        self.screen.refresh()

    def data(self, val: Word):
        # raise sys.exit("Data was written to!!!")
        row = self.address // self.width
        column = self.address % self.width
        self.text[row][column] = chr(val.val)
        self.address = (self.address + self.increment) % (self.width * self.height)
        self.render()

    def instruction(self, val: Word):
        msb = val.msb()
        # Clear display (Unknown time)
        if msb == 0:
            self.address = 0
            self.increment = 1
            self.text = [[' '] * self.width for _ in range(self.height)]

        # Return home (1.52ms)
        if msb == 1:
            self.address = 0

        # Entry mode set
        if msb == 2:
            self.increment = 1 if val[1] else -1

        self.render()


class Computer:
    def __init__(self, program: list[int], screen):
        self.L = Word(0)
        self.H = Word(0, bits=7)
        self.PC = Word(0, bits=15)
        self.X = Word(0)
        self.Y = Word(0)
        self.IN = Word(0)
        self.CF = False
        self.IF = False
        self.RAM = [Word(0)] * (2 ** 15)
        self.ROM = [Word(0)] * (2 ** 15)
        for i, instruction in enumerate(program):
            self.ROM[i] = Word(instruction)
        self.display = Display(screen)

    def terminated(self):
        return self.ROM[self.PC] == 0

    def input(self, val: int):
        self.IN = Word(val)
        self.IF = True

    def read_mem(self):
        """Gets the current memory value"""
        return self.RAM[self.H.concat(self.L)]

    def write_mem(self, value: Word):
        """Writes the given value to the current memory location"""
        self.RAM[self.H.concat(self.L)] = value

    def execute(self):
        """Executes a single instruction"""
        instruction = self.ROM[self.PC]

        # Halt instruction
        if instruction == 0:
            return

        self.PC += 1
        msb = instruction.msb()
        # Load byte instruction
        if msb == 7:
            self.L = Word(instruction[:7].val)

        # Arithmetic/Logic instruction
        if msb == 6:
            self.execute_al(instruction[5], instruction[4], instruction[:4])

        # Move instruction
        if msb == 5:
            source = instruction[:2].val
            if source == 3:
                source += instruction[4].val
            source_value = self.X
            if source == 1:
                source_value = self.L
            elif source == 2:
                source_value = self.IN
                self.IF = False
            elif source == 3:
                source_value = self.read_mem()
            elif source == 4:
                source_value = self.Y

            destination = instruction[2:4].val
            if destination == 3:
                destination += instruction[4].val
            if destination == 0:
                self.X = source_value
            elif destination == 1:
                self.L = source_value
            elif destination == 2:
                self.H = source_value[:7]
            elif destination == 3:
                self.Y = source_value
            elif destination == 4:
                self.write_mem(source_value)

        # Jump instruction
        if msb == 4:
            destination = self.H.concat(self.L)
            if instruction[3]:
                if instruction[0] and 0 < self.X < 127:
                    self.PC = destination
                if instruction[1] and self.X == 0:
                    self.PC = destination
                if instruction[2] and self.X >= 128:
                    self.PC = destination
            else:
                if instruction[1] and self.CF:
                    self.PC = destination
                if instruction[2] and self.IF:
                    self.PC = destination

        # Out instruction
        if msb == 3:
            source = instruction[:2]
            source_value = self.X
            if source == 1:
                source_value = self.L
            elif source == 2:
                source_value = self.IN
            elif source == 3:
                source_value = self.read_mem()

            if instruction[2]:
                self.display.data(source_value)
            else:
                self.display.instruction(source_value)

        # Carry instruction
        if msb == 1:
            if self.CF == bool(instruction[0]):
                self.H += 1

    def execute_al(self, out_x: Word, m: Word, opcode: Word):
        opcode = Word(OPCODE_MAPPING[opcode.val], bits=6)
        b = self.read_mem() if m else self.L
        x = self.X
        if opcode[5]:
            x = Word(0)
        if opcode[4]:
            x = ~x
        if opcode[3]:
            b = Word(0)
        if opcode[2]:
            b = ~b
        out = x + b if opcode[1] else x & b
        self.CF = out.carry if opcode[1] else self.CF
        if opcode[0]:
            out = ~out

        if out_x:
            self.X = out
        else:
            self.L = out
