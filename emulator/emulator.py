import curses

from .word import Word
from .disassembler import disassemble

TEXT = 1
WHITE = 2
GREY = 3
HIGHLIGHT_1 = 4
HIGHLIGHT_2 = 5

DISPLAY_HEIGHT = 24

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

ESC = 27
F5 = 269
F6 = 270
F12 = 276

BOX_VERT = '\u2503'
BOX_HOR = '\u2501'
BOX_BOTTOM_RIGHT = '\u251b'
BOX_BOTTOM_LEFT = '\u2517'
BOX_TOP_RIGHT = '\u2513'
BOX_TOP_LEFT = '\u250f'

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
                self.screen.addstr(i, 0, ''.join(line), curses.color_pair(TEXT))
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


class MemoryDisplay:
    def __init__(self, screen, data, data_display):
        self.data_display = data_display
        self.data = data
        self.screen = screen
        self.start = 0
        self.highlighted_element = -1
        self.alternative_highlight = -1

    def render(self):
        for line, i in enumerate(range(self.start, self.start + DISPLAY_HEIGHT)):
            if i == self.highlighted_element:
                color = HIGHLIGHT_1
            elif i == self.alternative_highlight:
                color = HIGHLIGHT_2
            elif i % 2 == 0:
                color = WHITE
            else:
                color = GREY
            self.screen.addstr(line, 0, f' {i:04x} ', curses.color_pair(color))
            try:
                format_string = f'{{:<{self.screen.getmaxyx()[1] - 6}s}}'
                self.screen.addstr(line, 6,
                                   format_string.format(self.data_display(self.data[i])), curses.color_pair(color))
            except curses.error:
                pass
        self.screen.refresh()

    def highlight_element(self, index: int):
        self.highlighted_element = index
        if self.highlighted_element < self.start or self.highlighted_element >= self.start + DISPLAY_HEIGHT:
            self.start = max(0, min(self.highlighted_element - 5, len(self.data) - DISPLAY_HEIGHT))

    def highlight_alternative_element(self, index: int):
        self.alternative_highlight = index


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

    def print_state(self):
        pass

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


def main(screen, program: list[int], debug: bool):
    screen.clear()
    curses.curs_set(False)
    curses.init_pair(TEXT, curses.COLOR_WHITE + 8, curses.COLOR_BLACK)
    curses.init_pair(WHITE, curses.COLOR_BLACK, curses.COLOR_WHITE + 8)
    curses.init_pair(GREY, curses.COLOR_BLACK, curses.COLOR_WHITE)
    curses.init_pair(HIGHLIGHT_1, curses.COLOR_BLACK, curses.COLOR_GREEN + 8)
    curses.init_pair(HIGHLIGHT_2, curses.COLOR_BLACK, curses.COLOR_CYAN + 8)

    # Draw box around input
    display = curses.newwin(9, 22)
    computer = Computer(program, display.subwin(4, 20, 1, 1))
    register_screen, rom_screen, ram_screen = None, None, None
    if debug:
        register_screen = curses.newwin(10, 20, 10, 0)
        ram_screen = MemoryDisplay(curses.newwin(24, 16, 0, 24), computer.RAM, lambda x: f' {x:02x} ({x})')
        rom_screen = MemoryDisplay(curses.newwin(24, 20, 0, 44), computer.ROM, lambda x: f' {x:02x} {disassemble(x)}')

    screen.refresh()
    display.addstr(0, 0, BOX_TOP_LEFT + (BOX_HOR * 20) + BOX_TOP_RIGHT, curses.color_pair(TEXT))
    display.addstr(5, 0, BOX_BOTTOM_LEFT + (BOX_HOR * 20) + BOX_BOTTOM_RIGHT, curses.color_pair(TEXT))
    for i in range(4):
        display.addstr(i + 1, 0, BOX_VERT, curses.color_pair(TEXT))
        display.addstr(i + 1, 21, BOX_VERT, curses.color_pair(TEXT))
    display.refresh()

    paused = True
    display.addstr(7, 0, f'{"PAUSED" if paused else "RUNNING":^22s}', curses.color_pair(TEXT))
    display.refresh()
    while True:
        if debug:
            register_screen.addstr(0, 0, f'PC: {computer.PC:04x} {f"({computer.PC})":<5s}', curses.color_pair(TEXT))
            register_screen.addstr(1, 0, f'L:    {computer.L:02x} {f"({computer.L})":<5s}', curses.color_pair(TEXT))
            register_screen.addstr(2, 0, f'H:    {computer.H:02x} {f"({computer.H})":<5s}', curses.color_pair(TEXT))
            register_screen.addstr(3, 0, f'X:    {computer.X:02x} {f"({computer.X})":<5s}', curses.color_pair(TEXT))
            register_screen.addstr(4, 0, f'Y:    {computer.Y:02x} {f"({computer.Y})":<5s}', curses.color_pair(TEXT))
            try:
                register_screen.addstr(5, 0,
                                       f'IN:   {computer.IN:02x} {f"({computer.IN})":<5s} [{chr(computer.IN.val)}]',
                                       curses.color_pair(TEXT))
            except ValueError:
                register_screen.addstr(5, 0, f'IN:   {computer.IN:02x} {f"({computer.IN})":<5s} [ ]',
                                       curses.color_pair(TEXT))
            register_screen.addstr(6, 0, f'CF={1 if computer.CF else 0}    IF={1 if computer.IF else 0}',
                                   curses.color_pair(TEXT))
            register_screen.refresh()
            a = computer.H.concat(computer.L).val
            rom_screen.highlight_element(computer.PC.val)
            rom_screen.highlight_alternative_element(a)
            rom_screen.render()
            ram_screen.highlight_element(a)
            ram_screen.render()

            key = screen.getch()
            if paused:
                while key not in [F5, F6, F12, ESC]:
                    key = screen.getch()

            if key == F5:
                paused = not paused
                display.addstr(7, 0, f'{"PAUSED" if paused else "RUNNING":^22s}', curses.color_pair(TEXT))
                display.refresh()
                screen.nodelay(not paused)

            if key == F12:
                computer.PC = Word(0, bits=15)

            if key == ESC:
                break

        if computer.terminated():
            display.addstr(6, 0, f'{"TERMINATED":^22s}', curses.color_pair(TEXT))
            display.refresh()
            screen.nodelay(False)
            key = screen.getch()
            while key not in [F12, ESC]:
                if key == F5:
                    paused = not paused
                    display.addstr(7, 0, f'{"PAUSED" if paused else "RUNNING":^22s}', curses.color_pair(TEXT))
                    display.refresh()
                key = screen.getch()

            if key == F12:
                computer.PC = Word(0, bits=15)
                display.addstr(6, 0, ' '*22)
                display.refresh()
                screen.nodelay(not paused)
                continue

            if key == ESC:
                break

        computer.execute()


def emulate(args):
    program = list(args.file.read())
    curses.wrapper(lambda screen: main(screen, program, args.debug))


def test():
    with open('/Users/nicholasprowse/Documents/Programming/HADLoC Programs/decimal/decimal.bin', 'rb') as f:
        program = list(f.read())
    computer = Computer(program, None)

    while computer.execute() or True:
        pass


if __name__ == '__main__':
    test()
