"""Presentation throttling must preserve the last value and transfer counts."""
from unittest.mock import Mock

from utils import download_progress


def test_first_interval_final_and_unchanged_values(monkeypatch):
    now = [0.0]
    monkeypatch.setattr(download_progress.time, 'monotonic', lambda: now[0])
    callback = Mock()
    reporter = download_progress.ProgressReporter(callback)
    reporter.update(1)
    reporter.update(2)
    now[0] = 0.11
    reporter.update(3)
    now[0] = 0.12
    reporter.update(4)
    reporter.finish()
    reporter.finish()
    now[0] = 1
    reporter.update(4)
    assert [call.args for call in callback.call_args_list] == [(1,), (3,), (4,)]


def test_finish_without_values_is_silent():
    callback = Mock()
    download_progress.ProgressReporter(callback).finish()
    callback.assert_not_called()
