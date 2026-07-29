"""Lifecycle guard for a yt-dlp subprocess.

The guard treats the configured timeout as process inactivity, not as a limit
on the total download duration.  Output lines and changes to known output files
are activity.  Stop/pause and inactivity share one termination gate so
concurrent monitors do not try to terminate the same process twice.
"""
from __future__ import annotations

import os
import subprocess
import threading
import time
from enum import Enum
from typing import Callable, Optional

from utils.logger import log

_UNINITIALIZED_FILE_STATE = object()


class TerminationReason(Enum):
    STOP_REQUESTED = "stop_requested"
    INACTIVITY_TIMEOUT = "inactivity_timeout"


class ProcessWatchdog:
    """Monitor stop requests and output inactivity for one subprocess."""

    _MAX_TRACKED_OUTPUT_FILES = 16
    _MAX_TRACKED_OUTPUT_DIRECTORIES = 4

    def __init__(
        self,
        process: subprocess.Popen,
        stop_check: Optional[Callable[[], bool]],
        terminate: Callable[[subprocess.Popen], None],
        inactivity_timeout: float,
        poll_interval: float,
    ):
        self._process = process
        self._stop_check = stop_check
        self._terminate = terminate
        self._inactivity_timeout = inactivity_timeout
        self._poll_interval = poll_interval

        self.stop_requested = threading.Event()
        self.inactivity_timed_out = threading.Event()
        self.termination_complete = threading.Event()

        self._closed = threading.Event()
        self._activity_condition = threading.Condition()
        self._last_activity = time.monotonic()
        self._file_poll_interval = min(
            1.0,
            max(self._poll_interval, self._inactivity_timeout / 4),
        )
        self._tracked_files_lock = threading.Lock()
        self._tracked_files: dict[str, object] = {}
        self._tracked_directories: dict[str, object] = {}
        self._termination_lock = threading.Lock()
        self._termination_reason: TerminationReason | None = None
        self._threads: list[threading.Thread] = []

    @property
    def termination_reason(self) -> TerminationReason | None:
        with self._termination_lock:
            return self._termination_reason

    def start(self) -> None:
        """Start inactivity and optional stop monitors."""
        inactivity_thread = threading.Thread(
            target=self._watch_inactivity,
            name="yt-dlp-inactivity-watchdog",
            daemon=True,
        )
        self._threads.append(inactivity_thread)
        inactivity_thread.start()

        file_thread = threading.Thread(
            target=self._watch_output_files,
            name="yt-dlp-output-file-monitor",
            daemon=True,
        )
        self._threads.append(file_thread)
        file_thread.start()

        if self._stop_check is not None:
            stop_thread = threading.Thread(
                target=self._watch_stop,
                name="yt-dlp-stop-monitor",
                daemon=True,
            )
            self._threads.append(stop_thread)
            stop_thread.start()

    def notify_activity(self) -> None:
        """Reset the inactivity deadline after receiving process output."""
        with self._activity_condition:
            self._last_activity = time.monotonic()
            self._activity_condition.notify_all()

    def watch_output_path(self, output_path: str) -> None:
        """Watch a known output and common yt-dlp/FFmpeg temporary variants."""
        if not output_path:
            return

        normalized_path = os.path.abspath(os.path.expanduser(output_path))
        candidate_paths = [normalized_path]
        if not normalized_path.lower().endswith(".part"):
            candidate_paths.append(f"{normalized_path}.part")
        path_root, path_extension = os.path.splitext(normalized_path)
        if path_extension:
            # yt-dlp's FFmpeg postprocessors commonly write beside the final
            # candidate using prepend_extension(path, "temp").
            candidate_paths.extend(
                (
                    f"{path_root}.temp{path_extension}",
                    f"{path_root}.part{path_extension}",
                )
            )

        with self._tracked_files_lock:
            for candidate_path in candidate_paths:
                if candidate_path in self._tracked_files:
                    continue
                while len(self._tracked_files) >= self._MAX_TRACKED_OUTPUT_FILES:
                    oldest_path = next(iter(self._tracked_files))
                    self._tracked_files.pop(oldest_path)
                self._tracked_files[candidate_path] = _UNINITIALIZED_FILE_STATE

    def watch_output_directory(self, output_directory: str) -> None:
        """Watch all output activity below one task-specific directory."""
        if not output_directory:
            return

        normalized_path = os.path.abspath(os.path.expanduser(output_directory))
        with self._tracked_files_lock:
            if normalized_path in self._tracked_directories:
                return
            while (
                len(self._tracked_directories)
                >= self._MAX_TRACKED_OUTPUT_DIRECTORIES
            ):
                oldest_path = next(iter(self._tracked_directories))
                self._tracked_directories.pop(oldest_path)
            self._tracked_directories[normalized_path] = (
                self._directory_snapshot(normalized_path)
            )

    def check_stop_requested(self) -> bool:
        """Poll the caller-provided stop predicate and record a stop request."""
        if self.stop_requested.is_set():
            return True
        if self._stop_check is None:
            return False

        try:
            requested = bool(self._stop_check())
        except Exception as exc:
            log.debug(f"stop_check monitor error: {exc}")
            return False

        if requested:
            self.request_stop()
            return True
        return False

    def request_stop(self) -> None:
        """Give an explicit stop/pause request priority in result reporting."""
        self.stop_requested.set()
        self._request_termination(TerminationReason.STOP_REQUESTED)

    def request_timeout(self) -> None:
        """Request termination because no process output arrived in time."""
        self._request_termination(TerminationReason.INACTIVITY_TIMEOUT)

    def wait_for_termination(self, timeout: float) -> bool:
        """Wait a bounded duration for the chosen termination action to finish."""
        if (
            self.termination_reason is None
            and not self.stop_requested.is_set()
            and not self.inactivity_timed_out.is_set()
        ):
            return True
        return self.termination_complete.wait(timeout=timeout)

    def close(self, join_timeout: float) -> None:
        """Stop monitor threads and wait for them for a bounded duration."""
        self._closed.set()
        with self._activity_condition:
            self._activity_condition.notify_all()

        for thread in self._threads:
            if thread is not threading.current_thread():
                thread.join(timeout=join_timeout)

    def _request_termination(self, reason: TerminationReason) -> None:
        should_terminate = self._claim_termination(reason)
        if should_terminate:
            try:
                self._terminate(self._process)
            finally:
                self.termination_complete.set()

    def _claim_termination(self, reason: TerminationReason) -> bool:
        with self._termination_lock:
            if (
                reason is TerminationReason.INACTIVITY_TIMEOUT
                and self.stop_requested.is_set()
            ):
                return False
            if self._termination_reason is None:
                self._termination_reason = reason
                if reason is TerminationReason.INACTIVITY_TIMEOUT:
                    self.inactivity_timed_out.set()
                return True
        return False

    def _watch_stop(self) -> None:
        while not self._closed.wait(self._poll_interval):
            if self._process.poll() is not None:
                return
            if self.check_stop_requested():
                return

    @staticmethod
    def _file_snapshot(path: str) -> tuple[int, int] | None:
        try:
            stat_result = os.stat(path)
        except OSError:
            return None
        return stat_result.st_size, stat_result.st_mtime_ns

    @staticmethod
    def _directory_snapshot(path: str) -> tuple[int, int, int] | None:
        """Return an aggregate snapshot that changes with files below path."""
        try:
            root_stat = os.stat(path)
        except OSError:
            return None

        entry_count = 1
        total_size = 0
        total_mtime_ns = root_stat.st_mtime_ns
        for directory, _subdirectories, filenames in os.walk(path):
            if os.path.abspath(directory) != path:
                try:
                    directory_stat = os.stat(directory)
                except OSError:
                    continue
                entry_count += 1
                total_mtime_ns += directory_stat.st_mtime_ns

            for filename in filenames:
                try:
                    file_stat = os.stat(os.path.join(directory, filename))
                except OSError:
                    continue
                entry_count += 1
                total_size += file_stat.st_size
                total_mtime_ns += file_stat.st_mtime_ns

        return entry_count, total_size, total_mtime_ns

    def _poll_file_activity(self) -> bool:
        with self._tracked_files_lock:
            tracked_files = list(self._tracked_files.items())

        changed = False
        for path, previous_snapshot in tracked_files:
            current_snapshot = self._file_snapshot(path)
            with self._tracked_files_lock:
                if (
                    path not in self._tracked_files
                    or self._tracked_files[path] != previous_snapshot
                ):
                    continue
                if previous_snapshot is _UNINITIALIZED_FILE_STATE:
                    self._tracked_files[path] = current_snapshot
                elif current_snapshot != previous_snapshot:
                    self._tracked_files[path] = current_snapshot
                    changed = True

        if changed:
            self.notify_activity()
        return changed

    def _poll_directory_activity(self) -> bool:
        with self._tracked_files_lock:
            tracked_directories = list(self._tracked_directories.items())

        changed = False
        for path, previous_snapshot in tracked_directories:
            current_snapshot = self._directory_snapshot(path)
            with self._tracked_files_lock:
                if (
                    path not in self._tracked_directories
                    or self._tracked_directories[path] != previous_snapshot
                ):
                    continue
                self._tracked_directories[path] = current_snapshot
                if current_snapshot != previous_snapshot:
                    changed = True

        if changed:
            self.notify_activity()
        return changed

    def _watch_output_files(self) -> None:
        while not self._closed.wait(self._file_poll_interval):
            self._poll_file_activity()
            self._poll_directory_activity()

    def _watch_inactivity(self) -> None:
        while not self._closed.is_set():
            with self._activity_condition:
                deadline = self._last_activity + self._inactivity_timeout
                remaining = deadline - time.monotonic()
                if remaining > 0:
                    self._activity_condition.wait(timeout=remaining)
                    continue

            if self._closed.is_set() or self._process.poll() is not None:
                return

            # A pause/cancel arriving on the timeout boundary wins over the
            # automatic timeout classification.
            if self.check_stop_requested():
                return

            # Recheck activity and process state at the termination gate.  A
            # line received while the deadline callback was being scheduled
            # starts a fresh inactivity window.
            with self._activity_condition:
                deadline = self._last_activity + self._inactivity_timeout
                if time.monotonic() < deadline:
                    continue
                if self._process.poll() is not None:
                    return
                should_terminate = self._claim_termination(
                    TerminationReason.INACTIVITY_TIMEOUT
                )

            if should_terminate:
                log.warning("yt-dlp produced no output before the inactivity deadline")
                try:
                    self._terminate(self._process)
                finally:
                    self.termination_complete.set()
            return
