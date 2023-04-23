from .tokenizer import tokenize
from .parser import Parser
from hadloc.utils import verify_file


def jcompile(file):
    """
    Compiles a J project into HADLoC assembly language.

    Args:
        file (TextIOWrapper): An open file representing the directory containing the J project to compile.

    Returns:
        str: The path of the assembly file created
    """
    file_name = verify_file(file, 'j', "File to compile must have a '.j' extension")
    tokens = tokenize(file)
    parser = Parser(tokens)
    parser.ast.print_tree()
