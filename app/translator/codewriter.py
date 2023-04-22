import os


class CodeWriter:

    def __init__(self, out, file):
        self.out = out
        self.static_vars = {}
        self.static_index = 20
        self.file = file
        self.label_num = 0

    @property
    def file(self):
        return self._file

    @file.setter
    def file(self, file):
        self._file = file
        if file not in self.static_vars:
            self.static_vars[file] = {}

    def write(self, *args, sep=' ', end='\n'):
        if type(args[0]) == list:
            for arg in args:
                if type(arg) == list:
                    self.write(*arg, sep=sep, end=end)
                else:
                    self.write(arg, sep=sep, end=end)
        else:
            for arg in args:
                self.out.write(str(arg) + sep)
            self.out.write(end)

    def get_static_address(self, index):
        if index not in self.static_vars[self.file]:
            self.static_vars[self.file][index] = self.static_index
            self.static_index += 1

        return self.static_vars[self.file][index]

    def load_sp(self, offset=0):
        if offset < 0:
            self.load_sp_neg(-offset)
            return

        self.write('lda sp[0]')
        self.write('mov M A')
        self.write('inc L L')
        self.write('mov M H')
        if offset > 1:
            self.write('ldb', offset)
            self.write('add A L L')
            self.write('carry')
        elif offset == 1:
            self.write('inc A L')
            self.write('carry')
        else:
            self.write('mov A L')

    def load_sp_neg(self, offset):
        if offset == 1:
            self.write(['lda sp[0]'],
                       'dec M A')
        else:
            self.write(['lda sp[0]'],
                       'mov M A',
                       ['ldb', offset],
                       'sub A L A')
        self.write(['lda L', self.label_num],
                   'jmpc',
                   'lda sp[1]',
                   'dec M B',
                   ['lda L', self.label_num + 1],
                   'jmp',
                   ['L', self.label_num, ':'],
                   'lda sp[1]',
                   'mov M B',
                   ['L', self.label_num + 1, ':'],
                   'mov B H',
                   'mov A L', sep='')
        self.label_num += 2

    def increment_sp(self, amount=1):
        if amount == 1:
            self.write(['lda sp[0]'],
                       'inc M A')
        else:
            self.write(['ldb', amount],
                       'mov L A',
                       'lda sp[0]',
                       'add A M A')
        self.write(['mov A M'],
                   ['lda L', self.label_num],
                   'jmpc',
                   ['lda L', self.label_num + 1],
                   'jmp',
                   ['L', self.label_num, ':'],
                   'lda sp[1]',
                   'inc M A',
                   'mov A M',
                   ['L', self.label_num + 1, ':'], sep='')
        self.label_num += 2

    def decrement_sp(self, amount=1):
        if amount == 1:
            self.write(['lda sp[0]'],
                       'dec M A')
        else:
            self.write(['ldb', amount],
                       'mov L A',
                       'lda sp[0]',
                       'sub M A A')
        self.write(['mov A M'],
                   ['lda L', self.label_num],
                   'jmpc',
                   'lda sp[1]',
                   'dec M A',
                   'mov A M',
                   ['L', self.label_num, ':'], sep='')
        self.label_num += 1

    def write_arithmetic(self, command):
        if command in ['add', 'sub', 'or', 'and']:
            self.decrement_sp(1)
            self.load_sp(-1)
            self.write(['mov M A'],
                       'inc L L',
                       'carry',
                       [command, 'A M A'],
                       'mov A M')

        if command in ['neg', 'not']:
            self.load_sp(-1)
            self.write(['mov M A'],
                       [command, 'A A'],
                       'mov A M')
        inequalities = {'lt': 'jlt', 'gt': 'jgt', 'eq': 'jeq', 'neq': 'jne', 'lte': 'jle', 'gte': 'jge'}
        if command in inequalities:
            self.decrement_sp(1)
            self.load_sp(-1)
            self.write(['mov M A'],
                       'inc L L',
                       'carry',
                       'sub A M A',
                       ['lda L', self.label_num],
                       inequalities[command],
                       'ldb 1',
                       'mov L B',
                       ['lda L', self.label_num + 1],
                       'jmp',
                       ['L', self.label_num, ':'],
                       'ldb 0',
                       'mov L B',
                       ['L', self.label_num + 1, ':'], sep='')
            self.load_sp(-1)
            self.write('mov B M')

    def write_push(self, seg, indices):
        indices = indices[::-1]
        if seg == 'in':
            self.write('mov I B')
            self.load_sp()
            self.write('mov B M')
            self.increment_sp()
            return

        if seg in ['pointer', 'temp']:
            for i in range(len(indices)):
                self.write(['lda', (10 if seg == 'temp' else 6) + indices[i]],
                           'mov M B')
                self.load_sp(i)
                self.write('mov B M')

        elif seg == 'static':
            for i in range(len(indices)):
                self.write(['lda', self.get_static_address(indices[i])],
                           'mov M B')
                self.load_sp(i)
                self.write('mov B M')

        elif seg == 'constant':
            self.write(['lda sp[0]'],
                       'mov M A',
                       'inc L L',
                       'mov M H')
            self.write(['ldb', indices[0]],
                       'mov L B',
                       'mov A L',
                       'mov B M')
            for i in range(1, len(indices)):
                self.write(['inc L A'],
                           'carry',
                           ['ldb', indices[i]],
                           'mov L B',
                           'mov A L',
                           'mov B M')

        elif seg in ['this', 'that', 'local', 'argument']:
            for i in range(len(indices)):
                self.write(['lda', seg, '[0]'],
                           ['mov M A'],
                           ['inc L L'],
                           ['mov M H'],
                           ['ldb', indices[i]],
                           ['add L A L'],
                           ['carry'],
                           ['mov M B'])
                self.load_sp(i)
                self.write('mov B M')

        self.increment_sp(len(indices))

    def write_pop(self, seg, indices):
        if seg == 'out':
            self.decrement_sp(indices[0])
            for i in range(indices[0]):
                self.load_sp(indices[0] - i - 1)
                self.write(['mov M L'],
                           'out')
            return

        self.decrement_sp(len(indices))
        for i in range(len(indices)):
            index = indices[i]
            self.load_sp(len(indices) - i - 1)
            self.write('mov M B')

            if seg in ['temp', 'pointer']:
                self.write(
                    ['lda', index + (10 if seg == 'temp' else 6)],
                    ['mov B M'])

            elif seg == 'static':
                self.write(
                    ['lda', self.get_static_address(index)],
                    ['mov B M'])

            elif seg in ['this', 'that', 'local', 'argument']:
                # Load address stored at this/that into L and H and add index
                self.write(
                    ['lda', seg, '[0]'],
                    ['mov M A'],
                    ['inc L L'],
                    ['mov M H'],
                    ['ldb', index],
                    ['add L A L'],
                    ['carry'],
                    ['mov B M'])


def main():
    os.chdir("/Users/nicholasprowse/Desktop")
    file = open('out.asm', 'w')
    writer = CodeWriter(file, "hello")
    writer.write_push('constant', [21, 62])
    writer.write_arithmetic('add')
    writer.write_pop('out', [1])
    file.close()


if __name__ == '__main__':
    main()
