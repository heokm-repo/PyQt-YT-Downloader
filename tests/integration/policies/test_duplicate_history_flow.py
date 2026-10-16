import pytest

from constants import TaskStatus
from data.duplicate_checker import DuplicateChecker
from data.history_store import HistoryManager
from data.models import DownloadTask
from gui.tasks.duplicate_check_target import DuplicateCheckTarget
from gui.tasks.single_video_download import review_single_video_duplicate
from gui.tasks.task_retry_plan import should_continue_retry_after_duplicate_check
from locales.strings import STR


@pytest.mark.parametrize('accepted', [False, True])
def test_retry_default_checker_preserves_history_until_confirmation(tmp_path, accepted):
    history = HistoryManager(tmp_path / 'history.db')
    history.add_to_history('Example', 'Case-ID', {}, 'webm')
    history.add_to_history('Example', 'Case-ID', {}, 'mp4')
    target = DuplicateCheckTarget('Example', 'Case-ID', 'webm')
    prompts = []
    assert should_continue_retry_after_duplicate_check(
        target, 1, [], history, None, confirm_duplicate=lambda message: prompts.append(message) or accepted
    ) == accepted
    assert prompts == [STR.MSG_DUP_ALREADY_DONE.format(format='webm') + STR.MSG_DUP_ASK_OVERWRITE]
    assert history.is_downloaded('Example', 'Case-ID', 'webm') == (not accepted)
    assert history.is_downloaded('Example', 'Case-ID', 'mp4')


def test_single_video_returns_first_active_duplicate_after_confirmation(tmp_path):
    history = HistoryManager(tmp_path / 'history.db')
    task = DownloadTask(3, '', video_id='same', extractor='youtube', status=TaskStatus.PAUSED)
    prompts = []
    result = review_single_video_duplicate(
        DuplicateChecker(history), DuplicateCheckTarget('youtube', 'same', 'mp4'), [task],
        lambda message: prompts.append(message) or True)
    assert not result.cancelled
    assert result.duplicate_task is task
    assert prompts == [STR.MSG_DUP_ALREADY_DONE.format(format='mp4')
                       + STR.MSG_DUP_IN_QUEUE.format(status=STR.STATUS_PAUSED) + STR.MSG_DUP_ASK_OVERWRITE]
