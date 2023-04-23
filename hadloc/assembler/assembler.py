from io import TextIOWrapper

from .tokenizer import Tokenizer
from .parser import Parser
from .label_encoder import encode_labels
from .codewriter import write_code

from hadloc.utils import path_without_extension


def assemble(file: TextIOWrapper):
    tokens = Tokenizer(file).run()
    instructions, warnings, labels = Parser(tokens).run()
    encode_labels(instructions, labels)
    files = write_code(instructions, path_without_extension(file))
    return warnings, files
