from io import TextIOWrapper

from .tokenizer import Tokenizer
from .parser import Parser
from .label_encoder import encode_labels
from .codewriter import write_code

from utils import verify_file


def assemble(file: TextIOWrapper):
    file_name = verify_file(file, 'hdc', "File must have '.hdc' extension")
    tokens = Tokenizer(file).run()
    instructions, warnings, labels = Parser(tokens).run()
    encode_labels(instructions, labels)
    files = write_code(instructions, file_name)
    return warnings, files
