"""Prevent silent English fallbacks and broken translated format templates."""
import importlib
from pathlib import Path
import sys

import pytest

from locales import SUPPORTED_LANGUAGES, get_language, set_language
from locales.strings import STR

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from tests.check_locales import audit_locales, english_defaults, format_fields


def test_all_catalogs_are_complete_and_all_references_resolve():
    report = audit_locales(ROOT)
    assert report['issues'] == []


@pytest.mark.parametrize('language', SUPPORTED_LANGUAGES)
def test_every_runtime_property_loads_its_translation_and_formats(language):
    defaults = dict(english_defaults(ROOT))
    values = defaults if language == 'en' else importlib.import_module(
        'locales.' + language.lower().replace('-', '_')).STRINGS
    previous = get_language()
    try:
        set_language(language)
        for key, expected in values.items():
            actual = getattr(STR, key)
            assert actual == expected, (language, key)
            # Existing templates use named fields without numeric format specs.
            fields = {name: 'test' for name, _, _ in format_fields(actual)}
            assert actual.format(**fields)
    finally:
        set_language(previous)


def test_format_audit_preserves_nested_and_repeated_fields():
    assert format_fields('{value:{width}} {value}') != format_fields('{value}')


def test_folder_notice_uses_language_selected_after_settings_load():
    from utils import settings_store
    from gui.dialogs.settings_fallback_notice import build_download_folder_fallback_message

    previous = get_language()
    previous_notice = settings_store._pending_download_folder_notice
    try:
        set_language('en')
        settings_store._set_download_folder_notice('old', 'new', STR.ERR_DOWNLOAD_FOLDER_PROTECTED)
        notice = settings_store.consume_download_folder_fallback_notice()
        set_language('ko')
        assert build_download_folder_fallback_message('{reason}', notice) == STR.ERR_DOWNLOAD_FOLDER_PROTECTED
        settings_store._set_download_folder_notice('old', 'new', 'OS diagnostic 123')
        notice = settings_store.consume_download_folder_fallback_notice()
        assert build_download_folder_fallback_message('{reason}', notice) == 'OS diagnostic 123'
    finally:
        settings_store._pending_download_folder_notice = previous_notice
        set_language(previous)


def test_download_errors_follow_language_changes_after_module_import(tmp_path, monkeypatch):
    from core.download import runner, media_discovery
    from core.download.finalization_pipeline import finalize_and_commit_download
    from core.download.finalization_verification import verify_finalized_output
    from core.download.finalization_policy import build_finalization_plan
    from core.download.media_probe import MediaProbeResult
    from gui.tasks.task_metadata_display import build_task_metadata_display
    from utils.bin.release_fetch import check_latest_github_release_strict, ReleaseCheckError
    from utils import app_updater
    from unittest.mock import Mock

    previous = get_language()
    try:
        for language in ('ko', 'ja', 'en'):
            set_language(language)
            assert runner.download_single_video_with_result('', {}, lambda *_: None).message == STR.ERR_INVALID_URL
            wrapper = Mock()
            wrapper.extract_info.return_value = (None, False)
            with pytest.raises(ValueError) as error:
                media_discovery.discover_media(wrapper, 'https://example.invalid', {}, tmp_path)
            assert str(error.value) == STR.ERR_MEDIA_DISCOVERY
            result = finalize_and_commit_download('', str(tmp_path), str(tmp_path), {}, None)
            assert result.error == STR.ERR_WORKSPACE_OUTPUT_MISSING
            plan = build_finalization_plan({'format': 'mp3'}, MediaProbeResult(audio_codec='aac'))
            assert verify_finalized_output(plan, MediaProbeResult(), MediaProbeResult()) == STR.ERR_FINAL_AUDIO_VERIFY
            assert build_task_metadata_display({}, {}).title_text == '[MP4] ' + STR.DEFAULT_VIDEO_TITLE
            response = Mock()
            response.json.return_value = []
            monkeypatch.setattr(app_updater.requests, 'get', Mock(return_value=response))
            with pytest.raises(app_updater.AppUpdateCheckError) as error:
                app_updater.check_for_updates_strict()
            assert str(error.value) == STR.ERR_RELEASE_INVALID_FMT.format(name='GitHub')
            with pytest.raises(ReleaseCheckError) as error:
                check_latest_github_release_strict('https://example.invalid', 'tool',
                                                  lambda _: ('1', 'https://example.invalid/file', None), '')
            assert str(error.value) == STR.ERR_RELEASE_TRUST_FMT.format(name='tool')
    finally:
        set_language(previous)
