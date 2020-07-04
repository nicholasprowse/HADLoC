
from .tokenizer import tokenize
from .parser import Parser
from .labelencoder import encode_labels
from .codewriter import write_code

from utils import verify_file


def assemble(file):
    file_name = verify_file(file, 'asm', "File must have '.asm' extension")
    tokens = tokenize(file)
    file.close()
    parser = Parser(tokens)
    encode_labels(parser)
    files = write_code(parser.instructions, file_name)
    return files
