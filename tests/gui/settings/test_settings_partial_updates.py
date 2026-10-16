"""Settings forms and window geometry share a file without losing unrelated keys."""
from unittest.mock import patch

import pytest

from constants import KEY_DOWNLOAD_FOLDER, KEY_THEME, THEME_DARK
from utils import settings_store
from utils.json_store import read_json, write_json_atomic


@pytest.fixture
def settings_file(tmp_path, monkeypatch):
    path = tmp_path / 'settings.json'
    monkeypatch.setattr(settings_store, 'settings_file_path', lambda: str(path))
    return path


def test_stale_form_preserves_latest_geometry_and_unrelated_keys(settings_file, tmp_path):
    original = {KEY_DOWNLOAD_FOLDER: str(tmp_path), KEY_THEME: THEME_DARK,
                'window_states': {'MainWindow': {'x': 10}}, 'unknown': '한글'}
    write_json_atomic(settings_file, original)
    stale_form = settings_store.load_settings()
    settings_store.update_settings({'window_states': {'MainWindow': {'x': 900}, 'Settings': {'x': 50}},
                                    'future_key': [1, 2]})
    stale_form['max_downloads'] = 3
    settings_store.save_settings(stale_form)
    saved = read_json(settings_file)
    assert saved['window_states'] == {'MainWindow': {'x': 900}, 'Settings': {'x': 50}}
    assert saved['unknown'] == '한글'
    assert saved['future_key'] == [1, 2]
    assert saved['max_downloads'] == 3


def test_partial_updates_merge_windows_without_folder_validation(settings_file):
    write_json_atomic(settings_file, {'window_states': {'MainWindow': {'x': 10}}, 'unknown': 'keep'})
    with patch.object(settings_store, '_ensure_writable_folder') as probe:
        settings_store.update_settings({'window_states': {'Settings': {'x': 30}}})
    probe.assert_not_called()
    assert read_json(settings_file) == {
        'window_states': {'MainWindow': {'x': 10}, 'Settings': {'x': 30}}, 'unknown': 'keep'}


def test_locked_settings_file_is_preserved_and_failure_logged(settings_file):
    write_json_atomic(settings_file, {'unknown': 'keep'})
    original = settings_file.read_bytes()
    with patch('utils.json_store.os.replace', side_effect=PermissionError('locked')), patch.object(settings_store, 'log') as log:
        settings_store.update_settings({'unknown': 'changed'})
    assert settings_file.read_bytes() == original
    log.error.assert_called_once()
