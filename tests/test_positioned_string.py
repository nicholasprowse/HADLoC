import pytest

from text_utils import PositionedString
from text_utils.positioned_string import Coordinate


@pytest.mark.parametrize(
    'text,raw,lines,columns',
    [
        ('define test 5', 'define test 5', [0] * 13, range(13)),
        ('define test 5\nldb test', 'define test 5ldb test', [0] * 13 + [1] * 8, list(range(13)) + list(range(8))),
        ('', '', [], []),
        ('\n\n\n', '', [], []),
        ('abc\ndef\nghi\njkl\n', 'abcdefghijkl', sum(([x]*3 for x in range(4)), start=[]), list(range(3))*4),
        ('abc\n\ndef\n', 'abcdef', [0]*3 + [2] * 3, list(range(3))*2)
    ]
)
@pytest.mark.parametrize('line_break', ['\n', '\r', '\r\n'])
def test_create_string(text, raw, lines, columns, line_break):
    string = PositionedString.create_string(text.replace('\n', line_break))
    assert string.text == raw
    assert [coordinate.line for coordinate in string.coordinates] == list(lines)
    assert [coordinate.column for coordinate in string.coordinates] == list(columns)


@pytest.mark.parametrize(
    'a,b,lt,eq,gt',
    [
        ('abc', 'abc', False, True, False),
        ('abc', 'abd', True, False, False),
        ('abc', 'abb', False, False, True),
        ('abc', 'abcc', True, False, False),
        ('abc', 'ab', False, False, True),
        ('abc', 'bb', True, False, False),
    ]
)
@pytest.mark.parametrize(
    'a_constructor,b_constructor',
    [
        (lambda a: a, lambda b: PositionedString.create_string(b)),
        (lambda a: PositionedString.create_string(a), lambda b: b),
        (lambda a: PositionedString.create_string(a), lambda b: PositionedString.create_string(b))
    ]
)
def test_comparison(a, b, lt, eq, gt, a_constructor, b_constructor):
    a, b = a_constructor(a), b_constructor(b)
    assert (a == b) == eq
    assert (a != b) == (not eq)
    assert (a < b) == lt
    assert (a <= b) == (lt or eq)
    assert (a > b) == gt
    assert (a >= b) == (gt or eq)


@pytest.mark.parametrize(
    'text,space,numeric,alpha,alnum',
    [
        ('', False, False, False, False),
        ('Hello World', False, False, False, False),
        ('jkb314  ', False, False, False, False),
        ('HelloWorld', False, False, True, True),
        (' \n\t\r\n    ', True, False, False, False),
        ('4083', False, True, False, True),
        ('3e9a1b', False, False, False, True),
        ('ihu23r7y89231', False, False, False, True)
    ]
)
def test_character_class_methods(text, space, numeric, alpha, alnum):
    text = PositionedString.create_string(text)
    assert text.isspace() == space
    assert text.isnumeric() == numeric
    assert text.isalpha() == alpha
    assert text.isalnum() == alnum


@pytest.mark.parametrize('a', ['', 'Hello World', 'jkb314  ', 'HelloWorld',
                               ' \n\t\r\n    ', '4083', '3e9a1b', 'ihu23r7y89231'])
@pytest.mark.parametrize('b', ['', 'Hello World', 'jkb314  ', 'HelloWorld',
                               ' \n\t\r\n    ', '4083', '3e9a1b', 'ihu23r7y89231'])
def test_hash(a, b):
    a = PositionedString.create_string(a)
    b = PositionedString.create_string(b)
    assert (a == b) == (hash(a) == hash(b))


@pytest.mark.parametrize(
    'element,collection,result',
    [
        ('a', ['a', 'b', 'c', 'abc'], True),
        ('d', ['a', 'b', 'c', 'abc'], False),
        ('a', {'a': 0, 'b': 1, 'c': 2, 'abc': 3}, True),
        ('d', {'a': 0, 'b': 1, 'c': 2, 'abc': 3}, False)
    ]
)
@pytest.mark.parametrize(
    'element_constructor,collection_constructor',
    [
        (lambda a: a, lambda b: PositionedString.create_string(b)),
        (lambda a: PositionedString.create_string(a), lambda b: b),
        (lambda a: PositionedString.create_string(a), lambda b: PositionedString.create_string(b))
    ]
)
def test_in_operator(element, collection, result, element_constructor, collection_constructor):
    element = element_constructor(element)
    if isinstance(collection, dict):
        collection = {collection_constructor(key): value for key, value in collection.items()}
    else:
        collection = [collection_constructor(x) for x in collection]
    assert (element in collection) == result


@pytest.mark.parametrize(
    'text,length',
    [
        ('', 0),
        ('He\rllo World', 11),
        ('jkb314  \r\n', 8),
        ('Hello\nWorld', 10),
        (' \n\t\r\n    ', 6),
        ('4083', 4),
        ('3e9a1b', 6),
        ('ihu23r\n7y89231', 13)
    ]
)
def test_len(text, length):
    assert len(PositionedString.create_string(text)) == length


@pytest.mark.parametrize(
    'text,value',
    [(str(i), i) for i in range(10)] +
    [(chr(i + ord('a')), i+10) for i in range(6)] +
    [(chr(i + ord('A')), i+10) for i in range(6)]
)
@pytest.mark.parametrize(
    'suffix',
    ['', 'He\rllo World', 'jkb314  \r\n', 'Hello\nWorld',
     ' \n\t\r\n    ', '4083', '3e9a1b', 'ihu23r\n7y89231']
)
def test_int(text, value, suffix):
    assert int(PositionedString.create_string(text + suffix)) == value


@pytest.mark.parametrize(
    'text',
    ['', 'He\rllo World', 'jkb314  \r\n', 'Hello\nWorld',
     ' \n\t\r\n    ', 'ihu23r\n7y89231']
)
def test_int_raises_exception(text):
    with pytest.raises(ValueError):
        int(PositionedString.create_string(text))


@pytest.mark.parametrize(
    'a,b,result',
    [
        (
            ('HelloWorld', [0] * 5 + [1] * 5, list(range(5))*2),
            ('More On Line 1', [1] * 14, list(range(14))),
            ('HelloWorldMore On Line 1', [0] * 5 + [1] * 19, list(range(5)) * 2 + list(range(14)))
        ),
        (
            ('HelloWorld', [6] * 5 + [3] * 5, list(range(5))*2),
            ('More On Line Different line', [100] * 27, list(range(10, 24))),
            ('HelloWorldMore On Line Different line', [6] * 5 + [3] * 5 + [100] * 27,
             list(range(5)) * 2 + list(range(10, 24)))
        )
    ]
)
def test_add(a, b, result):
    a = PositionedString(a[0], [Coordinate(x, y) for x, y in zip(a[1], a[2])])
    b = PositionedString(b[0], [Coordinate(x, y) for x, y in zip(b[1], b[2])])
    result = PositionedString(result[0], [Coordinate(x, y) for x, y in zip(result[1], result[2])])
    assert (a + b).text == result.text
    assert (a + b).coordinates == result.coordinates
    assert a + b == result


@pytest.mark.parametrize(
    'text,index,substring,lines,columns',
    [
        ('Hello\nWorld', 4, 'o', [0], [4]),
        ('Hello\nWorld', 5, 'W', [1], [0]),
        ('Hello\nWorld', -3, 'r', [1], [2]),
        ('Hello\nWorld', slice(2, 7), 'lloWo', [0, 0, 0, 1, 1], [2, 3, 4, 0, 1]),
        ('Hello\nWorld', slice(2, -1), 'lloWorl', [0, 0, 0, 1, 1, 1, 1], [2, 3, 4, 0, 1, 2, 3]),
        ('Hello\nWorld', slice(-3, -1), 'rl', [1, 1], [2, 3])
    ]
)
def test_get_item(text, index, substring, lines, columns):
    x = PositionedString.create_string(text)[index]
    coordinates = [Coordinate(*x) for x in zip(lines, columns)]
    assert x.text == substring
    assert x.coordinates == coordinates


@pytest.mark.parametrize(
    'text,lines,columns,index,line',
    [
        ('HelloWorld', [0] * 5 + [1] * 5, list(range(5))*2, 0, 0),
        ('HelloWorld', [0] * 5 + [1] * 5, list(range(5))*2, 3, 0),
        ('HelloWorld', [0] * 5 + [1] * 5, list(range(5))*2, 7, 1),
        ('HelloWorldMore On Line Different line', [6] * 5 + [3] * 5 + [100] * 27,
         list(range(5)) * 2 + list(range(10, 24)), 0, 6),
        ('HelloWorldMore On Line Different line', [6] * 5 + [3] * 5 + [100] * 27,
         list(range(5)) * 2 + list(range(10, 24)), 8, 3),
        ('HelloWorldMore On Line Different line', [6] * 5 + [3] * 5 + [100] * 27,
         list(range(5)) * 2 + list(range(10, 24)), 15, 100),
        ('HelloWorldMore On Line Different line', [6] * 5 + [3] * 5 + [100] * 27,
         list(range(5)) * 2 + list(range(10, 24)), 10, 100),
        ('HelloWorldMore On Line Different line', [6] * 5 + [3] * 5 + [100] * 27,
         list(range(5)) * 2 + list(range(10, 24)), -1, 100)
    ]
)
def test_line(text, lines, columns, index, line):
    text = PositionedString(text, [Coordinate(*x) for x in zip(lines, columns)])
    assert text.line(index) == line
