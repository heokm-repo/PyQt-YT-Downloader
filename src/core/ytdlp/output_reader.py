"""Bounded stdout handoff and disk-spooled, lossless stderr capture."""
from queue import Full, Queue
import tempfile
import threading


class StdoutReader:
    def __init__(self, stream, activity_hook=None, capacity=256):
        self.queue = Queue(maxsize=capacity)
        self.cancelled = threading.Event()
        self.stream = stream
        self.activity_hook = activity_hook
        self.thread = threading.Thread(target=self._read, name='yt-dlp-stdout-reader', daemon=True)

    def start(self):
        self.thread.start()

    def _put(self, item):
        while not self.cancelled.is_set():
            try:
                self.queue.put(item, timeout=0.05)
                return
            except Full:
                # Output is available but the consumer is applying backpressure;
                # this is not a silent/stalled subprocess.
                if self.activity_hook:
                    self.activity_hook()
                continue

    def _read(self):
        try:
            while not self.cancelled.is_set():
                line = self.stream.readline()
                if not line:
                    break
                if self.activity_hook:
                    self.activity_hook()
                self._put(('line', line))
        except (OSError, ValueError) as exc:
            self._put(('error', exc))
        finally:
            self._put(('eof', None))

    def close(self, timeout):
        # Wake a producer blocked on a full queue. Pipe reads finish after the
        # process terminates; never close a pipe under a running readline().
        self.cancelled.set()
        self.thread.join(timeout)
        if not self.thread.is_alive() and hasattr(self.stream, 'close'):
            self.stream.close()
        return not self.thread.is_alive()


class StderrCapture:
    """One writer; read only after the drain thread has joined."""
    def __init__(self):
        self.stream = tempfile.SpooledTemporaryFile(max_size=1024 * 1024, mode='w+t', encoding='utf-8', newline='')
        self.error = None

    def append(self, line):
        if self.error is None:
            try:
                self.stream.write(line)
            except OSError as exc:
                # Still drain the pipe if temporary storage is exhausted.
                self.error = exc

    def __iter__(self):
        self.stream.seek(0)
        return iter(self.stream)

    def close(self):
        self.stream.close()
