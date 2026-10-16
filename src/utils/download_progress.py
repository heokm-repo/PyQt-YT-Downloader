"""Throttle presentation callbacks without throttling transfer/cancel checks."""
import time


class ProgressReporter:
    def __init__(self, callback, interval=0.1):
        self.callback = callback
        self.interval = interval
        self._last_time = None
        self._sent = None
        self._pending = None

    def update(self, *values, force=False):
        self._pending = values
        if self.callback is None or values == self._sent:
            return
        now = time.monotonic()
        if force or self._last_time is None or now - self._last_time >= self.interval:
            self.callback(*values)
            self._sent = values
            self._last_time = now

    def finish(self):
        if self._pending is not None:
            self.update(*self._pending, force=True)
