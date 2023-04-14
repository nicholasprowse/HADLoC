from text_utils import Code
import pytest

from text_utils.positioned_string import Coordinate

lorem_ipsum = 'Lorem ipsum dolor sit amet,\n consectetur adipiscing elit.\n Donec mollis.'
length = len(lorem_ipsum.replace('\n', ''))


@pytest.mark.parametrize(
    'start,end,substring_length,relative,result',
    [
        (5, 13, None, False, ' ipsum d'),
        (None, 18, 9, False, 'um dolor '),
        (7, None, 3, False, 'psu'),
        (5, 13, None, True, 'or sit a'),
        (None, 18, 9, True, 'it amet, '),
        (7, None, 3, True, ' si'),
        (length - 5, None, 10, False, 'llis.')
    ]
)
def test_substring(start, end, substring_length, relative, result):
    code = Code(lorem_ipsum)
    code.offset = 10
    substring = code.substring(start, end, substring_length, relative)
    assert substring == result


@pytest.mark.parametrize(
    'offset,has_more',
    [
        (0, True),
        (20, True),
        (length - 1, True),
        (length, False),
        (length + 1, False),
    ]
)
def test_has_more(offset, has_more):
    code = Code(lorem_ipsum)
    code.offset = offset
    assert code.has_more() == has_more



@pytest.mark.parametrize(
    'offset,amount,result,result_offset',
    [
        (0, 1, 'L', 1),
        (0, 5, 'Lorem', 5),
        (10, 1, 'm', 11),
        (13, 3, 'olo', 16),
        (length - 2, 3, 's.', length),
        (length, 981724, '', length)
    ]
)
def test_advance(offset, amount, result, result_offset):
    code = Code(lorem_ipsum)
    code.offset = offset
    assert code.advance(amount) == result
    assert code.offset == result_offset


@pytest.mark.parametrize(
    'offset,match,result,result_offset',
    [
        (0, 'it', 'Lorem ipsum dolor sit', 21),
        (25, 'it', 't, consectetur adipiscing elit', 55),
        (0, 'kit', None, 0)
    ]
)
def test_advance_past(offset, match, result, result_offset):
    code = Code(lorem_ipsum)
    code.offset = offset
    assert code.advance_past(match) == result
    assert code.offset == result_offset


@pytest.mark.parametrize(
    'offset,match,result,result_offset',
    [
        (0, 'd', None, 0),
        (0, 'L', 'L', 1),
        (0, 'Lorem', 'Lorem', 5),
        (12, 'L', None, 12),
        (12, 'd', 'd', 13),
        (12, 'dolor', 'dolor', 17),
        (length - 1, '.', '.', length),
        (length, '.', None, length)
    ]
)
def test_match(offset, match, result, result_offset):
    code = Code(lorem_ipsum)
    code.offset = offset
    assert code.match(match) == result
    assert code.offset == result_offset


@pytest.mark.parametrize(
    'offset,lower,upper,result,result_offset',
    [
        (0, '0', '9', None, 0),
        (0, 'a', 'z', None, 0),
        (0, 'A', 'Z', 'L', 1),
        (12, '0', '9', None, 12),
        (12, 'a', 'z', 'd', 13),
        (12, 'A', 'Z', None, 12),
        (12, 'd', 'd', 'd', 13),
        (12, 'a', 'c', None, 12),
        (0, '\0', '\u00FF', 'L', 1),
        (length - 1, '\0', '\u00FF', '.', length),
        (length, '\0', '\u00FF', None, length)
    ]
)
def test_match_range(offset, lower, upper, result, result_offset):
    code = Code(lorem_ipsum)
    code.offset = offset
    assert code.match_range(lower, upper) == result
    assert code.offset == result_offset


@pytest.mark.parametrize(
    'offset,expected_len',
    [
        (0, length),
        (1, length - 1),
        (30, length - 30),
        (length - 5, 5),
        (length, 0)
    ]
)
def test_len(offset, expected_len):
    code = Code(lorem_ipsum)
    code.offset = offset
    assert len(code) == expected_len



@pytest.mark.parametrize(
    'offset,index,expected_char,expected_coordinates',
    [
        (0, 0, 'L', Coordinate(0, 0)),
        (0, 4, 'm', Coordinate(0, 4)),
        (4, 10, 'l', Coordinate(0, 14)),
        (10, -6, 'm', Coordinate(0, 4)),
        (length - 1, 0, '.', Coordinate(2, 13)),
        (length - 1, 10, '\0', Coordinate(2, 13)),
    ]
)
def test_get_item(offset, index, expected_char, expected_coordinates):
    code = Code(lorem_ipsum)
    code.offset = offset
    assert code[index] == expected_char
    assert code[index].coordinates == [expected_coordinates]


@pytest.mark.parametrize(
    'offset,expected_str',
    [
        (0, lorem_ipsum.replace('\n', '')),
        (5, lorem_ipsum.replace('\n', '')[5:]),
        (length - 1, '.'),
        (length, '')
    ]
)
def test_str(offset, expected_str):
    code = Code(lorem_ipsum)
    code.offset = offset
    assert str(code) == expected_str