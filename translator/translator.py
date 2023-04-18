from io import TextIOWrapper

from .parser import Parser
from .tokenizer import Tokenizer


def translate(file: TextIOWrapper):
    tokens = Tokenizer(file).run()
    parser = Parser(tokens)
    print(parser.ast)
    # instructions, labels = parse(tokens)
    # encode_labels(instructions, labels)
    # files = write_code(instructions, file_name[:-len(extension) - 1])
    return [], []

