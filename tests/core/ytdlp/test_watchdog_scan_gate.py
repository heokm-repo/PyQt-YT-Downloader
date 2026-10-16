import os
from types import SimpleNamespace
from unittest.mock import patch

from core.ytdlp.process_watchdog import ProcessWatchdog


def test_recent_output_skips_tree_scan_but_quiet_growth_still_counts(tmp_path):
    growing = tmp_path / 'unknown-merge.tmp'
    growing.write_bytes(b'x')
    watchdog = ProcessWatchdog(SimpleNamespace(poll=lambda: None), None, lambda _: None, 60, .1)
    watchdog.watch_output_directory(str(tmp_path))
    watchdog.watch_output_path(str(tmp_path / 'known.mp4'))
    with patch('core.ytdlp.process_watchdog.time.monotonic', return_value=100):
        watchdog.notify_activity()
        with patch.object(watchdog, '_poll_directory_activity', wraps=watchdog._poll_directory_activity) as scan:
            watchdog._poll_output_activity()
            scan.assert_not_called()
    with growing.open('ab') as stream:
        stream.write(b'grew quietly')
    with patch('core.ytdlp.process_watchdog.time.monotonic', return_value=102):
        watchdog._poll_output_activity()
    assert watchdog._last_activity == 102
    assert watchdog._last_output_activity == 100
    # File growth must not suppress the next tree scan for an unknown path.
    with patch('core.ytdlp.process_watchdog.time.monotonic', return_value=103), patch.object(
        watchdog, '_poll_directory_activity', wraps=watchdog._poll_directory_activity
    ) as scan:
        watchdog._poll_output_activity()
        scan.assert_called_once()
