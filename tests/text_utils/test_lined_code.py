from text_utils import LinedCode
import pytest

from text_utils.positioned_string import Coordinate

lorem_ipsum = 'Lorem ipsum dolor sit amet,\n consectetur adipiscing elit.\n Donec mollis.'
lines = lorem_ipsum.split('\n')
lengths = [len(x) for x in lines]
length = len(lorem_ipsum.replace('\n', ''))


@pytest.mark.parametrize(
    'start,end,substring_length,relative,result',
    [
        (5, 13, None, False, ' ipsum d'),
        (None, 18, 9, False, 'um dolor '),
        (7, None, 3, False, 'psu'),
        (5, 13, None, True, 'or sit a'),
        (None, 18, 9, True, 'it amet,'),
        (7, None, 3, True, ' si'),
        (length - 5, None, 10, False, '')
    ]
)
def test_substring(start, end, substring_length, relative, result):
    code = LinedCode(lorem_ipsum)
    code.offset = 10
    substring = code.substring(start, end, substring_length, relative)
    assert substring == result


@pytest.mark.parametrize(
    'offset,lines_skipped,has_more',
    [
        (0, 0, True),
        (20, 0, True),
        (lengths[0], 0, True),
        (length - 1, 0, True),
        (length, 0, True),
        (length + 1, 0, True),
        (length, 1, True),
        (lengths[2], 2, False),
        (10, 2, True),
    ]
)
def test_has_more(offset, lines_skipped, has_more):
    code = LinedCode(lorem_ipsum)
    for _ in range(lines_skipped):
        code.skip_line()
    code.offset = offset
    assert code.has_more() == has_more



@pytest.mark.parametrize(
    'offset,amount,result,result_offset',
    [
        (0, 1, 'L', 1),
        (0, 5, 'Lorem', 5),
        (10, 1, 'm', 11),
        (13, 3, 'olo', 16),
        (lengths[0] - 2, 3, 't,', lengths[0]),
        (lengths[0], 981724, '', lengths[0])
    ]
)
def test_advance(offset, amount, result, result_offset):
    code = LinedCode(lorem_ipsum)
    code.offset = offset
    assert code.advance(amount) == result
    assert code.offset == result_offset


@pytest.mark.parametrize(
    'offset,match,result,result_offset',
    [
        (0, 'it', 'Lorem ipsum dolor sit', 21),
        (25, 'it', None, 25),
        (0, 'kit', None, 0)
    ]
)
def test_advance_past(offset, match, result, result_offset):
    code = LinedCode(lorem_ipsum)
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
        (lengths[0] - 1, ',', ',', lengths[0]),
        (lengths[0], ',', None, lengths[0])
    ]
)
def test_match(offset, match, result, result_offset):
    code = LinedCode(lorem_ipsum)
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
        (lengths[0] - 1, '\0', '\u00FF', ',', lengths[0]),
        (lengths[0], '\0', '\u00FF', None, lengths[0])
    ]
)
def test_match_range(offset, lower, upper, result, result_offset):
    code = LinedCode(lorem_ipsum)
    code.offset = offset
    assert code.match_range(lower, upper) == result
    assert code.offset == result_offset


@pytest.mark.parametrize(
    'offset,expected_len',
    [
        (0, lengths[0]),
        (1, lengths[0] - 1),
        (30, 0),
        (lengths[0] - 5, 5),
        (lengths[0], 0)
    ]
)
def test_len(offset, expected_len):
    code = LinedCode(lorem_ipsum)
    code.offset = offset
    assert len(code) == expected_len



@pytest.mark.parametrize(
    'offset,index,expected_char,expected_coordinates',
    [
        (0, 0, 'L', Coordinate(0, 0)),
        (0, 4, 'm', Coordinate(0, 4)),
        (4, 10, 'l', Coordinate(0, 14)),
        (10, -6, 'm', Coordinate(0, 4)),
        (lengths[0] - 1, 0, ',', Coordinate(0, 26)),
        (lengths[0] - 1, 10, '\0', Coordinate(0, 26)),
    ]
)
def test_get_item(offset, index, expected_char, expected_coordinates):
    code = LinedCode(lorem_ipsum)
    code.offset = offset
    assert code[index] == expected_char
    assert code[index].coordinates == [expected_coordinates]


@pytest.mark.parametrize(
    'offset,expected_str',
    [
        (0, lorem_ipsum.split('\n')[0]),
        (5, lorem_ipsum.split('\n')[0][5:]),
        (lengths[0] - 1, ','),
        (lengths[0], '')
    ]
)
def test_str(offset, expected_str):
    code = LinedCode(lorem_ipsum)
    code.offset = offset
    assert str(code) == expected_str


@pytest.mark.parametrize('offset1', [0, 1, 7, lengths[0], 30])
@pytest.mark.parametrize('offset2', [0, 1, 10, lengths[1], 45])
@pytest.mark.parametrize('offset3', [0, 1, 5, lengths[2] - 1])
def test_skip_line(offset1, offset2, offset3):
    code = LinedCode(lorem_ipsum)

    code.offset = offset1
    assert code.text == lines[0]
    assert code.remaining_text == lines[1] + lines[2]
    assert code.has_more() == True
    assert code.skip_line() == True

    code.offset = offset2
    assert code.text == lines[1]
    assert code.remaining_text == lines[2]
    assert code.has_more() == True
    assert code.skip_line() == True

    code.offset = offset3
    assert code.text == lines[2]
    assert code.remaining_text == ''
    assert code.has_more() == True
    assert code.skip_line() == False

    assert code.remaining_text == ''
    assert code.has_more() == False


@pytest.mark.parametrize(
    'offset,line,result,expected_offset,expected_text,expected_remaining_text',
    [
        (0, 0, False, 0, lines[0], lines[1] + lines[2]),
        (0, 1, False, 0, lines[1], lines[2]),
        (0, 2, False, 0, lines[2], ''),
        (20, 0, False, 20, lines[0], lines[1] + lines[2]),
        (lengths[0] - 1, 0, False, lengths[0] - 1, lines[0], lines[1] + lines[2]),
        (lengths[0], 0, True, 0, lines[1], lines[2]),
        (20, 1, False, 20, lines[1], lines[2]),
        (lengths[1] - 1, 1, False, lengths[1] - 1, lines[1], lines[2]),
        (lengths[1], 1, True, 0, lines[2], ''),
        (20, 2, False, lengths[2], lines[2], ''),
        (lengths[2] - 1, 2, False, lengths[2] - 1, lines[2], ''),
        (lengths[2], 2, False, lengths[2], lines[2], '')
    ]
)
def test_advance_line(offset, line, result, expected_offset, expected_text, expected_remaining_text):
    code = LinedCode(lorem_ipsum)
    for _ in range(line):
        code.skip_line()
    code.offset = offset
    assert code.advance_line() == result
    assert code.offset == expected_offset
    assert code.text == expected_text
    assert code.remaining_text == expected_remaining_text