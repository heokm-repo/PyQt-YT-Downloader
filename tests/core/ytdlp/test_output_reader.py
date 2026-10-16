import io
import time
from types import SimpleNamespace
from unittest.mock import patch

from core.ytdlp.output_reader import StdoutReader, StderrCapture
from core.ytdlp.wrapper import YtDlpWrapper


def test_full_queue_cancel_wakes_reader_and_closes_stream():
    stream = io.StringIO('line\n' * 10000)
    reader = StdoutReader(stream, capacity=2)
    reader.start()
    deadline = time.monotonic() + 2
    while reader.queue.qsize() < 2 and time.monotonic() < deadline:
        time.sleep(.001)
    assert reader.queue.qsize() == 2
    assert reader.close(1)
    assert stream.closed


def test_bounded_reader_keeps_order_error_and_eof():
    class Stream:
        count = 0

        def readline(self):
            self.count += 1
            if self.count > 20:
                raise OSError('broken pipe')
            return str(self.count)

    reader = StdoutReader(Stream(), capacity=2)
    reader.start()
    try:
        values = [reader.queue.get(timeout=1) for _ in range(22)]
        assert values[:20] == [('line', str(i)) for i in range(1, 21)]
        assert values[-2][0] == 'error' and isinstance(values[-2][1], OSError)
        assert values[-1] == ('eof', None)
    finally:
        assert reader.close(1)


def test_spooled_stderr_reconstructs_full_diagnostic_without_truncation():
    capture = StderrCapture()
    text = ('한글 diagnostic\n' * 100000) + 'last error\n'
    try:
        for line in io.StringIO(text):
            capture.append(line)
        assert capture.stream._rolled
        with patch('core.ytdlp.wrapper.log'):
            result = YtDlpWrapper('unused')._result_from_process_exit(SimpleNamespace(returncode=3), capture)
        assert result == (False, 'yt-dlp exited with code 3: ' + text.strip())
    finally:
        capture.close()
    assert capture.stream.closed


def test_spool_storage_failure_keeps_draining_and_reports_capture_error():
    capture = StderrCapture()
    process = SimpleNamespace(stderr=io.StringIO('one\ntwo\nthree\n'), returncode=0)
    wrapper = YtDlpWrapper('unused')
    try:
        with patch.object(capture.stream, 'write', side_effect=OSError('disk full')):
            wrapper._drain_stderr(process, capture)
        assert process.stderr.tell() == len('one\ntwo\nthree\n')
        assert wrapper._result_from_process_exit(process, capture) == (
            False, 'Failed to capture yt-dlp stderr: disk full')
    finally:
        capture.close()
