"""Real local Python children exercise pipe/kill behavior without media/network."""
import sys
import threading
import time
from unittest.mock import patch

import pytest

from constants import MSG_PAUSED_BY_USER
from core.ytdlp.wrapper import YtDlpWrapper
from core.download.ffmpeg_process import run_ffmpeg_command


def child_command(code):
    return [sys.executable, '-u', '-c', code]


def assert_readers_gone(before):
    deadline = time.monotonic() + 2
    while time.monotonic() < deadline:
        readers = [t for t in threading.enumerate() if t.ident not in before and
                   t.name.startswith(('yt-dlp-', 'ffmpeg-'))]
        if not readers:
            return
        time.sleep(.01)
    assert not readers


def test_flood_preserves_markers_and_full_stderr_with_slow_consumer():
    wrapper = YtDlpWrapper('unused')
    code = """import sys
print('__YTDLP_METADATA__:{"id":"fixture"}')
for i in range(10000):
 print('ordinary line', i)
 sys.stderr.write('x' * 250 + '\\n')
print('__YTDLP_FINAL_PATH__:C:/fixture/한글.mp4')
sys.exit(3)
"""
    metadata = []
    before = {t.ident for t in threading.enumerate()}
    processes = []
    original_start = wrapper._start_download_process

    def start(args):
        proc = original_start(args)
        processes.append(proc)
        return proc

    count = 0

    def consume(line, current_file, last_progress, hook):
        nonlocal count
        count += 1
        if count % 100 == 0:
            time.sleep(.001)
        return last_progress

    with patch.object(wrapper, '_build_command', return_value=child_command(code)), patch.object(
        wrapper, '_start_download_process', side_effect=start
    ), patch.object(wrapper, '_emit_download_progress', side_effect=consume), patch('core.ytdlp.wrapper.log'):
        result = wrapper.download('offline', {}, lambda _: None, metadata_hook=metadata.append)
    assert result == (False, 'yt-dlp exited with code 3: ' + ('x' * 250 + '\n') * 9999 + 'x' * 250)
    assert metadata == [{'id': 'fixture'}]
    assert wrapper.final_output_path == 'C:/fixture/한글.mp4'
    assert processes[0].poll() == 3
    assert processes[0].stdout.closed and processes[0].stderr.closed
    assert_readers_gone(before)


@pytest.mark.parametrize('fail_first_kill', [False, True])
def test_cancel_flood_reaps_child_and_readers_even_after_failed_kill(fail_first_kill):
    wrapper = YtDlpWrapper('unused')
    code = "import sys\nwhile True:\n print('line' * 100)\n sys.stderr.write('error' * 100 + '\\n')"
    before = {t.ident for t in threading.enumerate()}
    stop = threading.Event()
    timer = threading.Timer(.1, stop.set)
    killed = []
    original = wrapper._kill_process

    def kill(process):
        killed.append(process)
        if not fail_first_kill or len(killed) > 1:
            original(process)

    timer.start()
    try:
        with patch.object(wrapper, '_build_command', return_value=child_command(code)), patch.object(
            wrapper, '_kill_process', side_effect=kill
        ), patch('core.ytdlp.wrapper.log'):
            result = wrapper.download('offline', {}, lambda _: None, stop_check=stop.is_set)
        assert result == (False, MSG_PAUSED_BY_USER)
        assert killed and killed[-1].poll() is not None
        assert wrapper.current_process is None
        assert_readers_gone(before)
    finally:
        timer.cancel()
        timer.join()
        for process in killed:
            if process.poll() is None:
                original(process)


@pytest.mark.parametrize('cancel', [False, True])
def test_metadata_process_is_reaped_on_success_or_cooperative_cancel(cancel):
    wrapper = YtDlpWrapper('unused')
    stop = threading.Event()
    code = "import time; time.sleep(5)" if cancel else 'print(\'{"id":"fixture"}\')'
    processes = []
    original_start = wrapper._start_download_process

    def start(args):
        proc = original_start(args)
        processes.append(proc)
        return proc

    timer = threading.Timer(.1, stop.set)
    if cancel:
        timer.start()
    try:
        with patch('core.ytdlp.wrapper.build_extract_info_command', return_value=child_command(code)), patch.object(
            wrapper, '_start_download_process', side_effect=start
        ):
            result = wrapper.extract_info('offline', stop_check=stop.is_set)
        assert result == ((None, False) if cancel else ({'id': 'fixture'}, True))
        assert processes[0].poll() is not None
        assert processes[0].stdout.closed and processes[0].stderr.closed
    finally:
        if cancel:
            timer.cancel()
            timer.join()
        for process in processes:
            if process.poll() is None:
                wrapper._kill_process(process)


def test_ffmpeg_flood_returns_identical_last_error_and_reaps_reader():
    before = {t.ident for t in threading.enumerate()}
    code = "import sys\nfor i in range(10000): sys.stderr.write('x' * 250 + '\\n')\nsys.stderr.write('  final error  \\n\\n'); sys.exit(2)"
    result = run_ffmpeg_command(child_command(code), stop_check=None, timeout_sec=10, timeout_error='timeout')
    assert not result.success and result.error == '  final error'
    assert_readers_gone(before)
