from io import TextIOWrapper

from .parser import vm_program
from .tokenizer import Tokenizer


def translate(file: TextIOWrapper):
    tokens = Tokenizer(file).run()
    ast = vm_program().parse(tokens)
    print(ast)
    # instructions, labels = parse(tokens)
    # encode_labels(instructions, labels)
    # files = write_code(instructions, file_name[:-len(extension) - 1])
    return [], []

