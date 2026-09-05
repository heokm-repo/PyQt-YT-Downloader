from unittest.mock import patch

import pytest

from core.download.options import _build_advanced_options, _build_playlist_extract_options
from utils.cookie_validation import is_usable_cookie_file


HEADER = "# Netscape HTTP Cookie File\n"
COOKIE = ".youtube.com\tTRUE\t/\tTRUE\t2000000000\tTEST\tvalue\n"


@pytest.mark.parametrize("content", ["", " \n\t", "garbage", HEADER,
    "\ufeff" + HEADER + COOKIE, HEADER + "invalid row\n",
    HEADER + COOKIE.replace("2000000000", "invalid")])
def test_invalid_cookies_are_omitted_from_download_and_playlist(tmp_path, content):
    path = tmp_path / "cookies.txt"
    path.write_text(content, encoding="utf-8")
    with patch("utils.cookie_store.get_cookie_file_path", return_value=str(path)), \
         patch("utils.bin.manager.get_quickjs_path", return_value=None):
        for builder in (_build_advanced_options, _build_playlist_extract_options):
            assert "cookiefile" not in builder({}, "https://youtube.com/watch?v=example")
    assert not path.exists()


@pytest.mark.parametrize("prefix", ["", "#HttpOnly_"])
def test_valid_cookies_remain_enabled(tmp_path, prefix):
    path = tmp_path / "cookies.txt"
    path.write_text(HEADER + prefix + COOKIE, encoding="utf-8")
    with patch("utils.cookie_store.get_cookie_file_path", return_value=str(path)), \
         patch("utils.bin.manager.get_quickjs_path", return_value=None):
        assert _build_advanced_options({}, "https://youtube.com/")["cookiefile"] == str(path)


def test_missing_directory_encoding_and_permission_errors(tmp_path):
    assert not is_usable_cookie_file(str(tmp_path / "missing"))
    assert not is_usable_cookie_file(str(tmp_path))
    path = tmp_path / "cookies.txt"
    path.write_bytes(b"\xff")
    assert not is_usable_cookie_file(str(path))
    with patch("builtins.open", side_effect=PermissionError):
        assert not is_usable_cookie_file(str(path))


def test_unreadable_cookie_is_not_deleted(tmp_path):
    path = tmp_path / "cookies.txt"
    path.write_text(HEADER + COOKIE, encoding="utf-8")
    with patch("builtins.open", side_effect=PermissionError):
        assert not is_usable_cookie_file(str(path), delete_invalid=True)
    assert path.exists()


def test_delete_failure_does_not_interrupt_download(tmp_path):
    path = tmp_path / "cookies.txt"
    path.write_text("", encoding="utf-8")
    with patch("utils.cookie_validation.os.remove", side_effect=PermissionError):
        assert not is_usable_cookie_file(str(path), delete_invalid=True)
    assert path.exists()
