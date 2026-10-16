from unittest.mock import Mock

import pytest

from constants import TaskStatus
from data.models import DownloadTask
from gui.tasks.download_completion import apply_failed_download_result, media_completion_summary
from gui.tasks.task_metadata_display import build_task_metadata_display
from gui.tasks.task_widget_restore import restore_task_widget_state
from locales import get_language, set_language, SUPPORTED_LANGUAGES
from locales.strings import STR


@pytest.fixture
def korean():
    before = get_language()
    set_language('ko')
    yield
    set_language(before)


def task_with_items(states):
    items = [{'kind': 'media', 'state': state, 'output_path': str(i) if state == 'completed' else ''}
             for i, state in enumerate(states)]
    items.extend([{'kind': 'image', 'state': 'skipped'}] * 4)
    return DownloadTask(1, 'url', meta={'title': '제목', 'media_items': items})


@pytest.mark.parametrize('states,expected', [
    (['completed'], '완료'), (['completed', 'completed'], '완료 [ 2 / 2 ]'),
])
def test_completed_text_and_restore_do_not_count_photos(korean, states, expected):
    task = task_with_items(states)
    assert media_completion_summary(task) == expected
    assert build_task_metadata_display(task.meta, {}).title_text == '[MP4] 제목'
    task.status = TaskStatus.FINISHED
    widget = Mock()
    restore_task_widget_state(widget, task)
    widget.status_label.setText.assert_called_once_with(expected)


@pytest.mark.parametrize('states,expected', [
    (['failed'], '실패 : 연결 오류'),
    (['completed', 'failed'], '실패 [ 1 / 2 ] : 연결 오류'),
    (['failed', 'failed'], '실패 [ 0 / 2 ] : 연결 오류'),
])
def test_failure_text_persists_across_task_restore(korean, states, expected):
    task = task_with_items(states)
    widget = Mock()
    apply_failed_download_result(task, widget, '연결 오류', STR.STATUS_PAUSED)
    widget.status_label.setText.assert_called_once_with(expected)
    assert task.meta['download_error'] == '연결 오류'
    restored = DownloadTask.from_dict(task.to_dict())
    new_widget = Mock()
    restore_task_widget_state(new_widget, restored)
    new_widget.status_label.setText.assert_called_once_with(expected)


def test_finalization_error_uses_korean_translation(korean):
    assert STR.ERR_MEDIA_FINALIZATION_FMT.format(error='오디오 없음') == '미디어 최종 처리 실패: 오디오 없음'


def test_new_templates_format_in_every_supported_language():
    before = get_language()
    try:
        for language in SUPPORTED_LANGUAGES:
            set_language(language)
            assert '[ 1 / 2 ]' in STR.STATUS_COMPLETED_COUNT.format(done=1, total=2)
            assert '[ 1 / 2 ]' in STR.STATUS_FAILED_COUNT_FMT.format(done=1, total=2, message='reason')
            assert 'reason' in STR.ERR_MEDIA_FINALIZATION_FMT.format(error='reason')
    finally:
        set_language(before)
