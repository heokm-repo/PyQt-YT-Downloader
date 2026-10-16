"""Cooperative cancellation for playlist metadata subprocesses."""
import subprocess
import time

from constants import PROCESS_MONITOR_INTERVAL_SEC


def communicate_cancellable(process, stop_check, timeout, terminate):
    """Drain both pipes while waiting; retain ownership until termination.

    A failed kill is retried. The QThread remains alive, so its GUI owner must
    defer destruction instead of abandoning a still-running child process.
    """
    deadline = time.monotonic() + timeout
    cancelled = False
    while True:
        if stop_check() or time.monotonic() >= deadline:
            cancelled = True
            terminate(process)
        try:
            stdout, stderr = process.communicate(timeout=PROCESS_MONITOR_INTERVAL_SEC)
            return None if cancelled else (stdout, stderr)
        except subprocess.TimeoutExpired:
            continue
