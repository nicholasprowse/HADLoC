from io import TextIOWrapper

from tokenizer import Tokenizer
from utils import verify_file


def translate(file: TextIOWrapper):
    file_name = verify_file(file, 'vm', "File must have '.vm' extension")
    tokens = Tokenizer(file).run()
    print(tokens)
    # instructions, labels = parse(tokens)
    # encode_labels(instructions, labels)
    # files = write_code(instructions, file_name[:-len(extension) - 1])
    print('Successfully Translated')

