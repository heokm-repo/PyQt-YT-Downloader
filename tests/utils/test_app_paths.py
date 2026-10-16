"""Path lookup remains independent from logging, binaries and Qt."""
import os
from pathlib import Path
import subprocess
import sys
from unittest.mock import patch

from utils import app_paths


def test_source_and_frozen_base_paths():
    with patch.object(sys, 'frozen', False, create=True):
        assert app_paths.get_base_path() == str(Path(app_paths.__file__).resolve().parents[1])
    with patch.object(sys, 'frozen', True, create=True), patch.object(sys, 'executable', 'C:/app/YTDownloader.exe'):
        assert app_paths.get_base_path() == 'C:/app'


def test_appdata_creation_and_unavailable_fallback(tmp_path, monkeypatch):
    monkeypatch.setenv(app_paths.APPDATA_ENV_VAR, str(tmp_path))
    assert app_paths.get_user_data_path() == str(tmp_path / app_paths.APPDATA_DIR_NAME)
    assert (tmp_path / app_paths.APPDATA_DIR_NAME).is_dir()
    monkeypatch.delenv(app_paths.APPDATA_ENV_VAR)
    assert app_paths.get_user_data_path() == app_paths.get_base_path()
    monkeypatch.setenv(app_paths.APPDATA_ENV_VAR, str(tmp_path / 'unavailable'))
    with patch.object(app_paths.os, 'makedirs', side_effect=PermissionError('blocked')):
        assert app_paths.get_user_data_path() == app_paths.get_base_path()


def test_compatibility_exports_are_the_same_functions():
    from utils import utils
    assert utils.get_base_path is app_paths.get_base_path
    assert utils.get_user_data_path is app_paths.get_user_data_path


def test_fresh_path_import_does_not_load_logger_manager_or_gui():
    source = str(Path(app_paths.__file__).resolve().parents[1])
    code = (
        'import sys; sys.path.insert(0, sys.argv[1]); import utils.app_paths; '
        'assert not any(n.startswith(("gui", "PyQt5", "utils.logger", "utils.bin")) '
        'for n in sys.modules)'
    )
    result = subprocess.run([sys.executable, '-B', '-c', code, source],
                            capture_output=True, encoding='utf-8', env=os.environ.copy())
    assert result.returncode == 0, result.stderr
