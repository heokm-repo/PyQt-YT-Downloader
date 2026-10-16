"""Atomic persistence must never expose a partially written replacement."""
from pathlib import Path
from unittest.mock import patch

import pytest

from utils import json_store


def test_roundtrip_uses_utf8_and_same_directory_replacement(tmp_path):
    destination = tmp_path / 'nested' / 'settings.json'
    replace = json_store.os.replace
    observed = []

    def record_replace(source, target):
        observed.append((Path(source).parent, Path(target)))
        replace(source, target)

    with patch.object(json_store.os, 'replace', side_effect=record_replace):
        json_store.write_json_atomic(destination, {'제목': '日本語 ✓'})
    assert json_store.read_json(destination) == {'제목': '日本語 ✓'}
    assert '日本語' in destination.read_text(encoding='utf-8')
    assert observed == [(destination.parent, destination)]
    assert list(destination.parent.iterdir()) == [destination]


@pytest.mark.parametrize('failure', ['serialize', 'write', 'fsync', 'replace'])
def test_failure_preserves_original_bytes_and_cleans_temporary_file(tmp_path, failure):
    destination = tmp_path / 'tasks.json'
    original = b'{"existing": true}\n'
    destination.write_bytes(original)

    def partial_write(value, stream, **kwargs):
        stream.write('{"partial":')
        raise OSError('disk full')

    if failure == 'serialize':
        operation = patch.object(json_store.json, 'dump', side_effect=TypeError('unsupported'))
    elif failure == 'write':
        operation = patch.object(json_store.json, 'dump', side_effect=partial_write)
    else:
        operation = patch.object(json_store.os, failure, side_effect=OSError('locked'))
    with operation, pytest.raises((OSError, TypeError)):
        json_store.write_json_atomic(destination, {'new': '내용'})
    assert destination.read_bytes() == original
    assert list(tmp_path.iterdir()) == [destination]


def test_invalid_utf8_is_left_to_the_callers_recovery_policy(tmp_path):
    destination = tmp_path / 'settings.json'
    destination.write_bytes(b'\xff{}')
    with pytest.raises(UnicodeError):
        json_store.read_json(destination)
