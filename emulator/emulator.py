import curses
import sys


TEXT = 1
WHITE = 2
GREY = 3
HIGHLIGHT_1 = 4
HIGHLIGHT_2 = 5


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
                self.screen.addstr(i, 0, ''.join(line))
            except curses.error:
                pass
        self.screen.refresh()

    def data(self, val):
        raise sys.exit("Data was written to!!!")
        # row = self.address // self.width
        # column = self.address % self.width
        # self.text[row][column] = chr(val)
        # self.address = (self.address + self.increment) % (self.width * self.height)
        # self.render()

    def instruction(self, val):
        # Clear display (Unknown time)
        if val == 1:
            self.address = 0
            self.increment = 1
            self.text = [[' '] * self.width for _ in range(self.height)]

        # Return home (1.52ms)
        if val in [2, 3]:
            self.address = 0

        # Entry mode set
        if val & 0xFC == 0x04:
            self.increment = 1 if val & 0x02 else -1

        self.render()


DISPLAY_HEIGHT = 24


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
                self.screen.addstr(line, 6, f'{self.data_display(self.data[i]):<10s}', curses.color_pair(color))
            except curses.error:
                pass
        self.screen.refresh()

    def highlight_element(self, index):
        self.highlighted_element = index
        if self.highlighted_element < self.start or self.highlighted_element >= self.start + DISPLAY_HEIGHT:
            self.start = max(0, min(self.highlighted_element - 5, len(self.data) - DISPLAY_HEIGHT))

    def highlight_alternative_element(self, index):
        self.alternative_highlight = index


class Computer:
    def __init__(self, program, screen):
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
        self.INSTRUCTION = 0
        self.display = Display(screen)

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
            srcval = self.X
            s = instruction & 0x10
            if src == 1:
                srcval = self.L
            elif src == 2:
                srcval = self.IN
            elif src == 3 and s:
                srcval = self.Y
            elif src == 3:
                srcval = self.read_mem()

            dst = (instruction >> 2) & 0x03
            if dst == 0:
                self.X = srcval
            elif dst == 1:
                self.L = srcval
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
            srcval = self.X
            s = instruction & 0x10
            if src == 1:
                srcval = self.L
            elif src == 2:
                srcval = self.IN
            elif src == 3 and s:
                srcval = self.Y
            elif src == 3:
                srcval = self.read_mem()

            if instruction & 0x04:
                self.display.data(srcval)
            else:
                self.display.instruction(srcval)

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

        return instruction != 0

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


def main(screen, program: list[int], debug: bool):
    screen.clear()
    curses.curs_set(False)
    curses.init_pair(TEXT, curses.COLOR_WHITE + 8, curses.COLOR_BLACK)
    curses.init_pair(WHITE, curses.COLOR_BLACK, curses.COLOR_WHITE + 8)
    curses.init_pair(GREY, curses.COLOR_BLACK, curses.COLOR_WHITE)
    curses.init_pair(HIGHLIGHT_1, curses.COLOR_BLACK, curses.COLOR_GREEN + 8)
    curses.init_pair(HIGHLIGHT_2, curses.COLOR_BLACK, curses.COLOR_CYAN + 8)

    display = curses.newwin(4, 20)
    computer = Computer(program, display)
    register_screen, rom_screen, ram_screen = None, None, None
    if debug:
        register_screen = curses.newwin(10, 20, 6, 0)
        rom_screen = MemoryDisplay(curses.newwin(24, 16, 0, 24), computer.ROM, lambda x: f'   {x:02x}')
        ram_screen = MemoryDisplay(curses.newwin(24, 16, 0, 44), computer.RAM, lambda x: f'  {x:02x} ({x})')

    screen.refresh()
    paused = True
    while True:
        if debug:
            register_screen.addstr(0, 0, f'PC: {computer.PC:04x} {f"({computer.PC})":<5s}')
            register_screen.addstr(1, 0, f'L:    {computer.L:02x} {f"({computer.L})":<5s}')
            register_screen.addstr(2, 0, f'H:    {computer.H:02x} {f"({computer.H})":<5s}')
            register_screen.addstr(3, 0, f'X:    {computer.X:02x} {f"({computer.X})":<5s}')
            register_screen.addstr(4, 0, f'Y:    {computer.Y:02x} {f"({computer.Y})":<5s}')
            try:
                register_screen.addstr(5, 0, f'IN:   {computer.IN:02x} {f"({computer.IN})":<5s} [{chr(computer.IN)}]')
            except ValueError:
                register_screen.addstr(5, 0, f'IN:   {computer.IN:02x} {f"({computer.IN})":<5s} [ ]')
            register_screen.addstr(6, 0, f'CF={1 if computer.CF else 0}    IF={1 if computer.IF else 0}')
            register_screen.refresh()
            a = computer.H << 8 | computer.L
            rom_screen.highlight_element(computer.PC)
            rom_screen.highlight_alternative_element(a)
            rom_screen.render()
            ram_screen.highlight_element(a)
            ram_screen.render()

            try:
                key = screen.getkey()
                while key not in ['KEY_F(5)', 'KEY_F(6)']:
                    key = screen.getkey()

                if key == 'KEY_F(5)':
                    paused = not paused
                    screen.nodelay(not paused)
            # Catch error thrown if there is no key press
            except curses.error:
                pass

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
