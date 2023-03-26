import curses

from .emulator import Computer
from .disassembler import disassemble
from .word import Word

TEXT = 1
WHITE = 2
GREY = 3
HIGHLIGHT_1 = 4
HIGHLIGHT_2 = 5
TEXT_RED = 6

KEY_QUIT = 27
KEY_PAUSE = curses.KEY_F5
KEY_STEP = curses.KEY_F6
KEY_RESET = curses.KEY_F12

BOX_VERT = '\u2503'
BOX_HOR = '\u2501'
BOX_BOTTOM_RIGHT = '\u251b'
BOX_BOTTOM_LEFT = '\u2517'
BOX_TOP_RIGHT = '\u2513'
BOX_TOP_LEFT = '\u250f'
BOX_T_LEFT = '\u2523'
BOX_T_RIGHT = '\u252b'

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


class RegisterDisplay:
    def __init__(self, computer, screen):
        self.computer = computer
        self.screen = screen

    def render(self):
        def render_reg(name, val):
            return f'{name}:    {val:02X} {f"({val})":<5s}'

        self.screen.addstr(0, 0, f'PC: {self.computer.PC:04X} {f"({self.computer.PC})":<5s}', curses.color_pair(TEXT))
        self.screen.addstr(1, 0, render_reg('L', self.computer.L), curses.color_pair(TEXT))
        self.screen.addstr(2, 0, render_reg('H', self.computer.H), curses.color_pair(TEXT))
        self.screen.addstr(3, 0, render_reg('X', self.computer.X), curses.color_pair(TEXT))
        self.screen.addstr(4, 0, render_reg('Y', self.computer.Y), curses.color_pair(TEXT))
        i = self.computer.IN
        try:
            self.screen.addstr(5, 0, f'IN:   {i:02X} {f"({i})":<5s} [{chr(i.val)}]', curses.color_pair(TEXT))
        except ValueError:
            self.screen.addstr(5, 0, f'IN:   {i:02X} {f"({i})":<5s} [ ]', curses.color_pair(TEXT))
        self.screen.addstr(6, 0, f'CF={1 if self.computer.CF else 0}    IF={1 if self.computer.IF else 0}',
                           curses.color_pair(TEXT))
        self.screen.refresh()


class IODisplay:
    def __init__(self, screen, controller):
        self.screen = screen
        self.input_screen = screen.subwin(1, 20, 1, 1)
        self.output_screen = screen.subwin(4, 20, 3, 1)
        self.controller = controller
        self.input_value = ''
        self.render_input()
        self.draw_outlines()
        self.screen.refresh()

    def render(self):

        terminated_string = 'TERMINATED' if self.controller.computer.terminated() else ''
        self.screen.addstr(8, 0, f'{terminated_string:^22s}', curses.color_pair(TEXT))

        if self.controller.debug:
            paused_message = 'PAUSED' if self.controller.paused else 'RUNNING'
            self.screen.addstr(9, 0, f'{paused_message:^22s}', curses.color_pair(TEXT))

        self.screen.refresh()

    def draw_outlines(self):
        self.screen.addstr(0, 0, BOX_TOP_LEFT + BOX_HOR * 20 + BOX_TOP_RIGHT, curses.color_pair(TEXT))
        self.screen.addstr(2, 0, BOX_T_LEFT + BOX_HOR * 20 + BOX_T_RIGHT, curses.color_pair(TEXT))
        self.screen.addstr(7, 0, BOX_BOTTOM_LEFT + BOX_HOR * 20 + BOX_BOTTOM_RIGHT, curses.color_pair(TEXT))
        for i in [1, 3, 4, 5, 6]:
            self.screen.addstr(i, 0, BOX_VERT, curses.color_pair(TEXT))
            self.screen.addstr(i, 21, BOX_VERT, curses.color_pair(TEXT))

    def process_key_press(self, key: int):
        if key == 127:
            self.input_value = self.input_value[:-1]
        elif key == 10:
            try:
                self.controller.computer.input(self.parse_input())
            except ValueError:
                pass
        elif key <= 255 and len(self.input_value) < 9:
            self.input_value += chr(key)
        self.render_input()

    def render_input(self):
        self.input_screen.addstr(0, 0, f'In: {self.input_value:<10s}', curses.color_pair(TEXT))
        try:
            try:
                parsed = self.parse_input()
                self.input_screen.addstr(0, 15, f' 0x{parsed:02X}', curses.color_pair(TEXT))
            except ValueError:
                self.input_screen.addstr(0, 15, 'ERROR', curses.color_pair(TEXT_RED))
        except curses.error:
            pass
        self.input_screen.refresh()

    def parse_input(self):
        if len(self.input_value) == 0:
            return 0
        if len(self.input_value) == 1:
            return ord(self.input_value)
        if self.input_value[0] == 'x':
            return int(self.input_value[1:], 16)
        if self.input_value[0] == 'b':
            return int(self.input_value[1:], 2)
        if self.input_value[0] == 'd':
            return int(self.input_value[1:])
        return int(self.input_value)


class Controller:
    def __init__(self, screen, program: list[int], debug: bool):
        self.screen = screen
        screen.refresh()
        self.debug = debug
        self.display = IODisplay(curses.newwin(11, 22), self)
        self.computer = Computer(program, self.display.output_screen)
        self.register_display = RegisterDisplay(self.computer, curses.newwin(10, 20, 11, 0))
        self.ram_screen = MemoryDisplay(curses.newwin(24, 16, 0, 24),
                                        self.computer.RAM, lambda x: f' {x:02x} ({x})')
        self.rom_screen = MemoryDisplay(curses.newwin(24, 20, 0, 44),
                                        self.computer.ROM, lambda x: f' {x:02x} {disassemble(x)}')
        self.paused = True
        self.screen.refresh()
        self.display.render()

    def render(self):
        if self.debug:
            self.register_display.render()
            a = self.computer.H.concat(self.computer.L).val
            self.rom_screen.highlight_element(self.computer.PC.val)
            self.rom_screen.highlight_alternative_element(a)
            self.rom_screen.render()
            self.ram_screen.highlight_element(a)
            self.ram_screen.render()

    def get_key(self):
        delay = (self.paused and self.debug) or self.computer.terminated()
        self.screen.nodelay(not delay)

        key = self.screen.getch()

        def valid_key():
            return key in [KEY_PAUSE, KEY_STEP, KEY_RESET, KEY_QUIT] or (key == curses.ERR and not delay)

        while not valid_key():
            key = self.screen.getch()

        if key == KEY_QUIT:
            raise SystemExit

        if key == KEY_RESET:
            self.computer.PC = Word(0, bits=15)
            self.display.render()

        if key == KEY_PAUSE:
            self.paused = not self.paused
            self.display.render()

        return key

    def step(self):
        self.render()
        if self.computer.terminated():
            self.display.render()

        delay = (self.paused and self.debug) or self.computer.terminated()
        self.screen.nodelay(not delay)
        key = self.screen.getch()

        if key == KEY_QUIT:
            raise SystemExit
        elif key == KEY_RESET:
            self.computer.PC = Word(0, bits=15)
            self.display.render()
        elif key == KEY_PAUSE:
            self.paused = not self.paused
            self.display.render()
        elif key == KEY_STEP or (key == curses.ERR and not delay):
            self.computer.execute()
        else:
            self.display.process_key_press(key)


def initialise_curses(screen):
    screen.clear()
    curses.curs_set(False)
    curses.init_pair(TEXT, curses.COLOR_WHITE + 8, curses.COLOR_BLACK)
    curses.init_pair(WHITE, curses.COLOR_BLACK, curses.COLOR_WHITE + 8)
    curses.init_pair(GREY, curses.COLOR_BLACK, curses.COLOR_WHITE)
    curses.init_pair(HIGHLIGHT_1, curses.COLOR_BLACK, curses.COLOR_GREEN + 8)
    curses.init_pair(HIGHLIGHT_2, curses.COLOR_BLACK, curses.COLOR_CYAN + 8)
    curses.init_pair(TEXT_RED, curses.COLOR_RED + 8, curses.COLOR_BLACK)


def main(screen, program: list[int], debug: bool):
    initialise_curses(screen)
    controller = Controller(screen, program, debug)
    while True:
        controller.step()


def start(args):
    program = list(args.file.read())
    curses.wrapper(lambda screen: main(screen, program, args.debug))
