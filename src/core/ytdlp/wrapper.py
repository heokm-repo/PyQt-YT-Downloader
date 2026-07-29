"""
yt-dlp.exe subprocess wrapper.
- Run yt-dlp.exe as an external process.
- Provide app-facing download and metadata methods.
- Parse stdout for progress updates.
"""
from __future__ import annotations

import os
import re
import subprocess
import threading
from json import JSONDecodeError, loads
from queue import Empty, Queue
from typing import Callable, Dict, List, Optional, Tuple

from constants import (
    DEFAULT_ENCODING,
    MSG_PAUSED_BY_USER,
    PROCESS_MONITOR_INTERVAL_SEC,
    PROCESS_TERMINATE_WAIT_SEC,
    THREAD_JOIN_SHORT_TIMEOUT_SEC,
    YTDLP_DOWNLOAD_PROCESS_TIMEOUT_SEC,
    YTDLP_FINAL_PATH_MARKER,
    YTDLP_METADATA_MARKER,
    YTDLP_TIMEOUT,
)
from core.ytdlp.command import build_command
from core.ytdlp.info_command import build_extract_info_command
from core.ytdlp.info_parser import parse_info_output
from core.ytdlp.process_watchdog import ProcessWatchdog
from core.ytdlp.progress import parse_progress
from utils.logger import log
from utils.url_security import redact_url_for_log, redact_urls_in_text


def _ytdlp_environment() -> dict[str, str]:
    """Return an isolated UTF-8 environment for the external yt-dlp process."""
    environment = os.environ.copy()
    environment["YTDLP_NO_PLUGINS"] = "1"
    environment["PYTHONIOENCODING"] = DEFAULT_ENCODING
    return environment


class YtDlpWrapper:
    """Wrap the managed external yt-dlp executable."""

    def __init__(self, ytdlp_path: str, ffmpeg_path: Optional[str] = None):
        """
        Args:
            ytdlp_path: yt-dlp.exe path.
            ffmpeg_path: Optional ffmpeg.exe path.
        """
        self.ytdlp_path = ytdlp_path
        self.ffmpeg_path = ffmpeg_path
        self.current_process: Optional[subprocess.Popen] = None
        self.final_output_path: Optional[str] = None
        self._process_kill_lock = threading.Lock()

        self.destination_pattern = re.compile(
            r'\[(?:download|ExtractAudio|VideoConvertor|VideoRemuxer|ffmpeg)\]'
            r'.*?\bDestination:\s*"?(.+?)"?$'
        )
        self.merger_pattern = re.compile(r'\[Merger\] Merging formats into\s*"(.+?)"$')
        self.complete_pattern = re.compile(r'\[download\] 100%')

    def _download_creation_flags(self) -> int:
        if os.name == 'nt':
            return subprocess.CREATE_NO_WINDOW | subprocess.CREATE_NEW_PROCESS_GROUP
        return 0

    def _start_download_process(self, args: List[str]) -> subprocess.Popen:
        process = subprocess.Popen(
            args,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding=DEFAULT_ENCODING,
            errors='replace',
            creationflags=self._download_creation_flags(),
            env=_ytdlp_environment(),
        )
        self.current_process = process
        return process

    def _kill_process(self, process: subprocess.Popen) -> None:
        """Terminate a process forcefully."""
        with self._process_kill_lock:
            try:
                if process and process.poll() is None:
                    if os.name == 'nt':
                        try:
                            subprocess.run(
                                ['taskkill', '/F', '/T', '/PID', str(process.pid)],
                                capture_output=True,
                                creationflags=subprocess.CREATE_NO_WINDOW,
                                timeout=PROCESS_TERMINATE_WAIT_SEC,
                                check=True,
                            )
                        except (OSError, subprocess.SubprocessError) as exc:
                            log.debug(
                                f"taskkill failed for pid={process.pid}, "
                                f"falling back to process.kill(): {exc}"
                            )
                            try:
                                process.kill()
                            except OSError as kill_error:
                                log.debug(
                                    f"process.kill fallback failed for pid={process.pid}: "
                                    f"{kill_error}"
                                )
                    else:
                        try:
                            process.kill()
                        except OSError as kill_error:
                            log.debug(f"process.kill failed for pid={process.pid}: {kill_error}")

                    try:
                        process.wait(timeout=PROCESS_TERMINATE_WAIT_SEC)
                    except subprocess.TimeoutExpired as exc:
                        log.debug(f"Process did not exit after kill (pid={process.pid}): {exc}")
                    except OSError as exc:
                        log.debug(f"Process wait after kill failed (pid={process.pid}): {exc}")
            except (OSError, subprocess.SubprocessError) as exc:
                log.debug(f"Process termination cleanup failed: {exc}")
            finally:
                if self.current_process is process:
                    self.current_process = None

    def _drain_stderr(
        self,
        process: subprocess.Popen,
        output_list: list[str],
        activity_hook: Callable[[], None] | None = None,
    ) -> None:
        try:
            for line in iter(process.stderr.readline, ''):
                if line:
                    if activity_hook:
                        activity_hook()
                    output_list.append(line)
        except (OSError, ValueError) as exc:
            log.debug(f"stderr drain stopped: {exc}")

    def _start_stderr_drain(
        self,
        process: subprocess.Popen,
        output_list: list[str],
        activity_hook: Callable[[], None] | None = None,
    ) -> threading.Thread:
        thread = threading.Thread(
            target=self._drain_stderr,
            args=(process, output_list, activity_hook),
            daemon=True,
        )
        thread.start()
        return thread

    def _emit_destination_progress(
        self,
        line: str,
        current_file: Optional[str],
        progress_hook: Callable,
    ) -> Optional[str]:
        dest_match = self.destination_pattern.search(line)
        if dest_match:
            current_file = dest_match.group(1)
            log.info(f"Downloading/Processing to: {current_file}")
            if '[download]' not in line:
                progress_hook({'status': 'postprocessing', 'filename': current_file})

        merger_match = self.merger_pattern.search(line)
        if merger_match:
            current_file = merger_match.group(1)
            log.info(f"Merging formats into: {current_file}")
            progress_hook({'status': 'postprocessing', 'filename': current_file})

        return current_file

    def _emit_download_progress(
        self,
        line: str,
        current_file: Optional[str],
        last_progress: dict,
        progress_hook: Callable,
    ) -> dict:
        progress_data = self._parse_progress(line)
        if progress_data:
            if current_file:
                progress_data['filename'] = current_file
            if progress_data != last_progress:
                progress_hook(progress_data)
                return progress_data.copy()
        return last_progress

    def _emit_completion_progress(
        self,
        line: str,
        current_file: Optional[str],
        progress_hook: Callable,
    ) -> None:
        if self.complete_pattern.search(line):
            log.info("Download complete")
            progress_hook({'status': 'finished', 'filename': current_file})

    def _emit_metadata(self, line: str, metadata_hook: Callable[[Dict], None] | None) -> bool:
        """Parse and dispatch a marked metadata line without exposing its raw JSON."""
        if not line.startswith(YTDLP_METADATA_MARKER):
            return False

        if metadata_hook is None:
            return True

        try:
            metadata = loads(line[len(YTDLP_METADATA_MARKER):])
        except (JSONDecodeError, TypeError):
            log.warning("Failed to parse yt-dlp metadata output")
            return True

        if not isinstance(metadata, dict):
            log.warning("Ignoring non-object yt-dlp metadata output")
            return True

        try:
            metadata_hook(metadata)
        except Exception as exc:
            log.warning(f"yt-dlp metadata hook failed ({type(exc).__name__})")

        return True

    def _run_stdout_progress_loop(
        self,
        process: subprocess.Popen,
        progress_hook: Callable,
        stop_check: Callable[[], bool] | None,
        metadata_hook: Callable[[Dict], None] | None = None,
        process_watchdog: ProcessWatchdog | None = None,
    ) -> bool:
        current_file = None
        last_progress: dict = {}
        stdout_queue: Queue[tuple[str, object | None]] = Queue()

        def read_stdout() -> None:
            try:
                for raw_line in iter(process.stdout.readline, ''):
                    if raw_line:
                        if process_watchdog:
                            process_watchdog.notify_activity()
                        stdout_queue.put(("line", raw_line))
            except (OSError, ValueError) as exc:
                stdout_queue.put(("error", exc))
            finally:
                stdout_queue.put(("eof", None))

        stdout_thread = threading.Thread(
            target=read_stdout,
            name="yt-dlp-stdout-reader",
            daemon=True,
        )
        stdout_thread.start()

        try:
            while True:
                # A stop request has priority when it lands on the same
                # monitoring tick as the inactivity deadline.
                if process_watchdog:
                    if process_watchdog.check_stop_requested():
                        return True
                    if process_watchdog.inactivity_timed_out.is_set():
                        return False
                elif stop_check and stop_check():
                    log.info("Stop/pause detected via stop_check, killing process forcefully")
                    self._kill_process(process)
                    return True

                try:
                    item_type, item = stdout_queue.get(
                        timeout=PROCESS_MONITOR_INTERVAL_SEC
                    )
                except Empty:
                    continue

                if item_type == "error":
                    if isinstance(item, BaseException):
                        raise item
                    raise RuntimeError("yt-dlp stdout reader failed")
                if item_type == "eof":
                    if process_watchdog:
                        if process_watchdog.check_stop_requested():
                            return True
                        if process_watchdog.inactivity_timed_out.is_set():
                            return False
                    break

                raw_line = str(item)
                line = raw_line.strip()
                if line.startswith(YTDLP_FINAL_PATH_MARKER):
                    self.final_output_path = line[len(YTDLP_FINAL_PATH_MARKER):]
                    if process_watchdog:
                        process_watchdog.watch_output_path(self.final_output_path)
                    log.info(f"Final output path: {self.final_output_path}")
                    continue
                if self._emit_metadata(line, metadata_hook):
                    continue
                previous_file = current_file
                current_file = self._emit_destination_progress(line, current_file, progress_hook)
                if (
                    process_watchdog
                    and current_file
                    and current_file != previous_file
                ):
                    process_watchdog.watch_output_path(current_file)
                last_progress = self._emit_download_progress(
                    line,
                    current_file,
                    last_progress,
                    progress_hook,
                )
                self._emit_completion_progress(line, current_file, progress_hook)
        except Exception as hook_error:
            if MSG_PAUSED_BY_USER in str(hook_error):
                log.info("Progress hook requested download interruption")
            else:
                log.error("Progress loop failed, killing process forcefully", exc_info=True)
            self._kill_process(process)
            raise hook_error
        finally:
            self._join_thread(stdout_thread, PROCESS_MONITOR_INTERVAL_SEC)

        return False

    def _join_thread(self, thread: threading.Thread | None, timeout: float) -> None:
        if thread:
            thread.join(timeout=timeout)

    def _watchdog_result(
        self,
        process_watchdog: ProcessWatchdog,
    ) -> Tuple[bool, str] | None:
        """Return a stop/timeout result after bounded termination completion."""
        if (
            not process_watchdog.stop_requested.is_set()
            and not process_watchdog.inactivity_timed_out.is_set()
        ):
            return None

        termination_wait = (
            PROCESS_TERMINATE_WAIT_SEC * 2
            + THREAD_JOIN_SHORT_TIMEOUT_SEC
        )
        if not process_watchdog.wait_for_termination(termination_wait):
            log.warning("Timed out waiting for yt-dlp termination cleanup")

        if process_watchdog.stop_requested.is_set():
            return False, MSG_PAUSED_BY_USER
        return False, "Download timeout"

    def _wait_for_download_result(
        self,
        process: subprocess.Popen,
        stderr_output: list[str],
        stderr_thread: threading.Thread,
        process_watchdog: ProcessWatchdog,
    ) -> Tuple[bool, str]:
        watchdog_result = self._watchdog_result(process_watchdog)
        if watchdog_result:
            self._join_thread(stderr_thread, PROCESS_TERMINATE_WAIT_SEC)
            return watchdog_result

        while True:
            watchdog_result = self._watchdog_result(process_watchdog)
            if watchdog_result:
                self._join_thread(stderr_thread, PROCESS_TERMINATE_WAIT_SEC)
                return watchdog_result
            try:
                process.wait(timeout=PROCESS_MONITOR_INTERVAL_SEC)
                break
            except subprocess.TimeoutExpired:
                continue

        watchdog_result = self._watchdog_result(process_watchdog)
        if watchdog_result:
            self._join_thread(stderr_thread, PROCESS_TERMINATE_WAIT_SEC)
            return watchdog_result

        self.current_process = None
        self._join_thread(stderr_thread, PROCESS_TERMINATE_WAIT_SEC)
        return self._result_from_process_exit(process, stderr_output)

    def _result_from_process_exit(
        self,
        process: subprocess.Popen,
        stderr_output: list[str],
    ) -> Tuple[bool, str]:
        stderr = ''.join(stderr_output).strip()
        if stderr:
            log.warning(f"yt-dlp stderr: {redact_urls_in_text(stderr)}")

        if process.returncode != 0:
            error_msg = f"yt-dlp exited with code {process.returncode}"
            if stderr:
                error_msg += f": {redact_urls_in_text(stderr)}"
            log.error(error_msg)
            return False, error_msg

        return True, "Download complete"

    def download(
        self,
        url: str,
        options: Dict,
        progress_hook: Callable,
        is_resume: bool = False,
        stop_check: Callable | None = None,
        metadata_hook: Callable[[Dict], None] | None = None,
    ) -> Tuple[bool, str]:
        """
        Download a video through the managed external yt-dlp executable.

        Args:
            url: Download URL.
            options: yt-dlp option dictionary.
            progress_hook: Progress callback.
            is_resume: Whether the task is being resumed.
            stop_check: Callback returning True when the process should stop.
            metadata_hook: Optional callback for metadata emitted before download.

        Returns:
            (success, error message)
        """
        process = None
        stderr_output: list[str] = []
        process_watchdog: ProcessWatchdog | None = None
        self.final_output_path = None

        try:
            args = self._build_command(url, options, is_resume)
            logged_args = [redact_url_for_log(arg) if arg == url else arg for arg in args]
            log.info(f"Running yt-dlp: {' '.join(logged_args)}")

            process = self._start_download_process(args)
            process_watchdog = ProcessWatchdog(
                process=process,
                stop_check=stop_check,
                terminate=self._kill_process,
                inactivity_timeout=YTDLP_DOWNLOAD_PROCESS_TIMEOUT_SEC,
                poll_interval=PROCESS_MONITOR_INTERVAL_SEC,
            )
            watched_directories: set[str] = set()
            for option_name in ("temp_path", "home_path"):
                output_directory = str(options.get(option_name) or "")
                if output_directory and output_directory not in watched_directories:
                    process_watchdog.watch_output_directory(output_directory)
                    watched_directories.add(output_directory)
            process_watchdog.start()
            stderr_thread = self._start_stderr_drain(
                process,
                stderr_output,
                process_watchdog.notify_activity,
            )

            stopped = self._run_stdout_progress_loop(
                process,
                progress_hook,
                stop_check,
                metadata_hook,
                process_watchdog,
            )
            if stopped:
                watchdog_result = self._watchdog_result(process_watchdog)
                self._join_thread(stderr_thread, PROCESS_TERMINATE_WAIT_SEC)
                return watchdog_result or (False, MSG_PAUSED_BY_USER)

            return self._wait_for_download_result(
                process,
                stderr_output,
                stderr_thread,
                process_watchdog,
            )
        except subprocess.SubprocessError as exc:
            self._kill_process(process)
            error_msg = f"Subprocess error: {exc}"
            log.error(error_msg)
            return False, error_msg
        except Exception as exc:
            self._kill_process(process)
            error_msg = f"Unexpected error: {exc}"
            log.error(error_msg)
            return False, error_msg
        finally:
            if process_watchdog:
                process_watchdog.close(THREAD_JOIN_SHORT_TIMEOUT_SEC)

    def extract_info(
        self,
        url: str,
        options: Optional[Dict] = None,
    ) -> Tuple[Optional[Dict], bool]:
        """
        Extract metadata through the managed external yt-dlp executable.

        Args:
            url: YouTube URL.
            options: Additional options.

        Returns:
            (metadata dict, success)
        """
        try:
            args = build_extract_info_command(self.ytdlp_path, url, options)

            logged_args = [redact_url_for_log(arg) if arg == url else arg for arg in args]
            log.info(f"Extracting info: {' '.join(logged_args)}")

            result = subprocess.run(
                args,
                capture_output=True,
                text=True,
                encoding=DEFAULT_ENCODING,
                errors='replace',
                timeout=YTDLP_TIMEOUT,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0,
                env=_ytdlp_environment(),
            )

            if result.returncode != 0:
                log.error(f"extract_info failed: {redact_urls_in_text(result.stderr)}")
                return None, False

            return parse_info_output(result.stdout)

        except subprocess.TimeoutExpired:
            log.error("extract_info timeout")
            return None, False
        except JSONDecodeError as exc:
            log.error(f"JSON parse error: {exc}")
            return None, False
        except Exception as exc:
            log.error(f"extract_info error: {exc}", exc_info=True)
            return None, False

    def _parse_progress(self, line: str) -> Optional[Dict]:
        """Parse yt-dlp stdout progress while preserving the existing API."""
        return parse_progress(line)

    def _build_command(self, url: str, options: Dict, is_resume: bool = False) -> List[str]:
        """Convert yt-dlp option dicts to CLI arguments while preserving the existing API."""
        return build_command(self.ytdlp_path, self.ffmpeg_path, url, options, is_resume)
