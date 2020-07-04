import os
from error import CompilerException, FileError
from tokenizer import tokenize


def translate(file_name):
    extension = file_name[len(file_name) - file_name[::-1].find('.'):]
    if extension != 'vm':
        raise FileError(file_name, "Can only assemble VM language files with the extension '.vm'")
    try:
        file = open(file_name)
    except FileNotFoundError:
        raise FileError(file_name, "File not found")
    tokens = tokenize(file)
    file.close()
    print(tokens)
    # instructions, labels = parse(tokens)
    # encode_labels(instructions, labels)
    # files = write_code(instructions, file_name[:-len(extension) - 1])
    print('Successfully Translated')


def main():
    os.chdir("/Users/nicholasprowse/Desktop")
    try:
        translate("rnd.vm")
    except CompilerException as ce:
        ce.display()


if __name__ == '__main__':
    main()
