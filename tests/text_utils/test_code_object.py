import pytest
from unittest.mock import sentinel

from text_utils import PositionedString, CodeObject, add
from text_utils.positioned_string import Coordinate


def constructor(name):
    if name == 'PositionedString':
        return lambda x: PositionedString.create_string(x[0])
    if name == 'CodeObject':
        return lambda x: CodeObject(x[0], PositionedString.create_string(x[1]))
    return lambda x: x[0]


@pytest.mark.parametrize(
    'a,b,expected_string',
    [
        (PositionedString.create_string('Hello'), PositionedString.create_string('\nWorld'),
         PositionedString.create_string('Hello\nWorld')),
        (PositionedString.create_string('Hello'), PositionedString.create_string('World'),
         PositionedString('HelloWorld', [Coordinate(0, x) for x in list(range(5)) * 2])),
        (PositionedString.create_string('Hello\n\n'), PositionedString.create_string('World'),
         PositionedString('HelloWorld', [Coordinate(0, x) for x in list(range(5)) * 2])),
        (PositionedString.create_string('Hello'), PositionedString.create_string('\n\nWorld'),
         PositionedString.create_string('Hello\n\nWorld'))
    ]
)
def test_add_operator(a, b, expected_string):
    result = CodeObject(sentinel.value, a) + CodeObject(sentinel.ignored, b)
    assert result.value == sentinel.value
    assert result.text == expected_string.text
    assert result.coordinates == expected_string.coordinates


@pytest.mark.parametrize(
    'a,b,expected_string',
    [
        (PositionedString.create_string('Hello'), PositionedString.create_string('\nWorld'),
         PositionedString.create_string('Hello\nWorld')),
        (PositionedString.create_string('Hello'), PositionedString.create_string('World'),
         PositionedString('HelloWorld', [Coordinate(0, x) for x in list(range(5)) * 2])),
        (PositionedString.create_string('Hello\n\n'), PositionedString.create_string('World'),
         PositionedString('HelloWorld', [Coordinate(0, x) for x in list(range(5)) * 2])),
        (PositionedString.create_string('Hello'), PositionedString.create_string('\n\nWorld'),
         PositionedString.create_string('Hello\n\nWorld'))
    ]
)
def test_add_function(a, b, expected_string):
    def func(x, y): return sentinel.value
    result = add(CodeObject(sentinel.value_a, a), CodeObject(sentinel.value_b, b), func)
    assert result.value == sentinel.value
    assert result.text == expected_string.text
    assert result.coordinates == expected_string.coordinates


@pytest.mark.parametrize('a', ['', 'Hello World', 'jkb\n314'])
@pytest.mark.parametrize('b', ['', 'Hello World', 'jkb\n314'])
@pytest.mark.parametrize('value_a', ['Hello', 124, 0, ''])
@pytest.mark.parametrize('value_b', ['Hello', 124, 0, ''])
def test_hash(a, b, value_a, value_b):
    a = CodeObject(value_a, PositionedString.create_string(a))
    b = CodeObject(value_b, PositionedString.create_string(b))
    assert (a != b) or (hash(a) == hash(b))  # a == b => hash(a) == hash(b)


@pytest.mark.parametrize(
    'element,collection,result',
    [
        (('y', 'ignored'), [('x', 'a'), ('y', 'b'), ('z', 'c'), ('xyz', 'abc')], True),
        (('w', 'ignored'), [('x', 'a'), ('y', 'b'), ('z', 'c'), ('xyz', 'abc')], False),
        (('y', 'ignored'), {('x', 'a'): 0, ('y', 'b'): 1, ('z', 'c'): 2, ('xyz', 'abc'): 3}, True),
        (('w', 'ignored'), {('x', 'a'): 0, ('y', 'b'): 1, ('z', 'c'): 2, ('xyz', 'abc'): 3}, False),
    ]
)
@pytest.mark.parametrize(
    'element_constructor,collection_constructor',
    [
        ('CodeObject', 'str'),
        ('CodeObject', 'PositionedString'),
        ('str', 'CodeObject'),
        ('PositionedString', 'CodeObject'),
        ('CodeObject', 'CodeObject'),
    ]
)
def test_in_operator(element, collection, result, element_constructor, collection_constructor):
    element = constructor(element_constructor)(element)
    if isinstance(collection, dict):
        collection = {constructor(collection_constructor)(key): value for key, value in collection.items()}
    else:
        collection = [constructor(collection_constructor)(x) for x in collection]
    assert (element in collection) == result


def test_none():
    none = CodeObject.none()
    assert none.value is None
    assert none.text == ''
    assert none.coordinates == []

    none = CodeObject.none(PositionedString(sentinel.text, sentinel.coordinates))
    assert none.value is None
    assert none.text == sentinel.text
    assert none.coordinates == sentinel.coordinates


@pytest.mark.parametrize('a', [('', '1'), ('Hello World', '2'), ('jkb314', '3')])
@pytest.mark.parametrize('b', [('', '4'), ('Hello World', '5'), ('jkb314', '6')])
@pytest.mark.parametrize(
    'a_constructor,b_constructor',
    [
        ('CodeObject', 'str'),
        ('CodeObject', 'PositionedString'),
        ('str', 'CodeObject'),
        ('PositionedString', 'CodeObject'),
        ('CodeObject', 'CodeObject'),
    ]
)
def test_eq(a, b, a_constructor, b_constructor):
    assert (a[0] == b[0]) == (constructor(a_constructor)(a) == constructor(b_constructor)(b))
