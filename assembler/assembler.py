from io import TextIOWrapper

from .tokenizer import tokenize
from .parser import Parser
from .label_encoder import encode_labels
from .codewriter import write_code

from utils import verify_file


def assemble(file: TextIOWrapper):
    file_name = verify_file(file, 'hdc', "File must have '.hdc' extension")
    tokens = tokenize(file)
    file.close()
    warnings = []
    parser = Parser(tokens, warnings)
    warnings = ["Warning: " + warning for warning in warnings]
    encode_labels(parser)
    files = write_code(parser.instructions, file_name)
    return warnings, files
