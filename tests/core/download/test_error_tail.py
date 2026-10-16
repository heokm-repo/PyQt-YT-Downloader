import io
import pytest

from core.download.error_tail import LastErrorLine


@pytest.mark.parametrize('text', [
    '', ' \n\t', '  only error  \n', 'old\n  final error  \n\n\t',
    '\n\n  only error\n', 'old\rnew\r\n  마지막 오류  ',
    'first\vsecond\fthird\x1cfourth\x85fifth\u2028sixth\u2029last\n',
    'line\n' * 10000 + '  final', '   no newline', 'one\n \n',
], ids=['empty', 'blank', 'single', 'trailing-blanks', 'leading-blanks',
        'crlf', 'unicode-separators', 'flood', 'no-newline', 'trailing-space'])
def test_last_line_preserves_previous_error_contract(text):
    tail = LastErrorLine()
    for record in io.StringIO(text):
        tail.append(record)
    assert tail.value == (text.strip().splitlines()[-1] if text.strip() else '')
