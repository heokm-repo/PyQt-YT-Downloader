import pytest

from constants import TaskStatus
from data.duplicate_checker import DuplicateResult
from data.models import DownloadTask
from gui.dialogs.main_window_messages import duplicate_overwrite_message
from locales import SUPPORTED_LANGUAGES, get_language, set_language
from locales.strings import STR


@pytest.mark.parametrize('language', SUPPORTED_LANGUAGES)
@pytest.mark.parametrize('status', [None, TaskStatus.WAITING, TaskStatus.DOWNLOADING, TaskStatus.PAUSED])
def test_duplicate_wording_matches_previous_flow_in_every_language(language, status):
    previous = get_language()
    try:
        set_language(language)
        task = DownloadTask(1, '', status=status) if status is not None else None
        result = DuplicateResult(True, 'webm', task, status)
        expected = STR.MSG_DUP_ALREADY_DONE.format(format='webm')
        if status is not None:
            status_text = {TaskStatus.WAITING: STR.STATUS_WAITING_DOTS,
                           TaskStatus.DOWNLOADING: STR.STATUS_DOWNLOADING_DOTS,
                           TaskStatus.PAUSED: STR.STATUS_PAUSED}[status]
            expected += STR.MSG_DUP_IN_QUEUE.format(status=status_text)
        expected += STR.MSG_DUP_ASK_OVERWRITE
        assert duplicate_overwrite_message(result) == expected
    finally:
        set_language(previous)
