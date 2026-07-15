"""
yt-dlp.exe subprocess wrapper.
- Run yt-dlp.exe as an external process.
- Provide app-facing download and metadata methods.
- Parse stdout for progress updates.
"""
from __future__ import annotations

from dataclasses import dataclass
import os
import re
import subprocess
import threading
import time
from json import JSONDecodeError
from typing import Callable, Dict, List, Optional, Tuple

from constants import (
    DEFAULT_ENCODING,
    MSG_PAUSED_BY_USER,
    PROCESS_MONITOR_INTERVAL_SEC,
    PROCESS_TERMINATE_WAIT_SEC,
    THREAD_JOIN_SHORT_TIMEOUT_SEC,
    YTDLP_DOWNLOAD_PROCESS_TIMEOUT_SEC,
    YTDLP_FINAL_PATH_MARKER,
    YTDLP_TIMEOUT,
)
from core.ytdlp.command import build_command
from core.ytdlp.info_command import build_extract_info_command
from core.ytdlp.info_parser import parse_info_output
from core.ytdlp.progress import convert_to_bytes, parse_eta, parse_progress
from utils.logger import log
from utils.url_security import redact_url_for_log, redact_urls_in_text


def _ytdlp_environment() -> dict[str, str]:
    """Return an isolated UTF-8 environment for the external yt-dlp process."""
    environment = os.environ.copy()
    environment["YTDLP_NO_PLUGINS"] = "1"
    environment["PYTHONIOENCODING"] = DEFAULT_ENCODING
    return environment


@dataclass(frozen=True)
class ProgressLoopResult:
    current_file: Optional[str]
    last_progress: dict
    stopped: bool = False


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

        self.destination_pattern = re.compile(
            r'\[(?:download|ExtractAudio|VideoConvertor|ffmpeg)\] Destination:\s*"?(.+?)"?$'
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

    def _kill_process(self, process: subprocess.Popen, graceful: bool = False) -> None:
        """Terminate a process gracefully or forcefully."""
        try:
            if process and process.poll() is None:
                if graceful and os.name == 'nt':
                    import signal
                    try:
                        os.kill(process.pid, signal.CTRL_BREAK_EVENT)
                        process.wait(timeout=PROCESS_TERMINATE_WAIT_SEC)
                        return
                    except subprocess.TimeoutExpired as exc:
                        log.debug(f"Graceful process termination timed out (pid={process.pid}): {exc}")
                    except OSError as exc:
                        log.debug(f"Graceful process termination failed (pid={process.pid}): {exc}")

                if os.name == 'nt':
                    try:
                        subprocess.run(
                            ['taskkill', '/F', '/T', '/PID', str(process.pid)],
                            capture_output=True,
                            creationflags=subprocess.CREATE_NO_WINDOW,
                        )
                    except (OSError, subprocess.SubprocessError) as exc:
                        log.debug(f"taskkill failed for pid={process.pid}, falling back to process.kill(): {exc}")
                        try:
                            process.kill()
                        except OSError as kill_error:
                            log.debug(f"process.kill fallback failed for pid={process.pid}: {kill_error}")
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
            self.current_process = None

    def _drain_stderr(self, process: subprocess.Popen, output_list: list[str]) -> None:
        try:
            for line in iter(process.stderr.readline, ''):
                if line:
                    output_list.append(line)
        except (OSError, ValueError) as exc:
            log.debug(f"stderr drain stopped: {exc}")

    def _start_stderr_drain(
        self,
        process: subprocess.Popen,
        output_list: list[str],
    ) -> threading.Thread:
        thread = threading.Thread(
            target=self._drain_stderr,
            args=(process, output_list),
            daemon=True,
        )
        thread.start()
        return thread

    def _start_stop_monitor(
        self,
        process: subprocess.Popen,
        stop_check: Callable[[], bool] | None,
        stop_requested: threading.Event,
    ) -> threading.Thread | None:
        if not stop_check:
            return None

        def watch_stop() -> None:
            while process.poll() is None:
                try:
                    if stop_check():
                        stop_requested.set()
                        log.info("Stop/pause detected by monitor, killing process forcefully")
                        self._kill_process(process, graceful=False)
                        return
                except Exception as exc:
                    log.debug(f"stop_check monitor error: {exc}")
                time.sleep(PROCESS_MONITOR_INTERVAL_SEC)

        thread = threading.Thread(target=watch_stop, daemon=True)
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

    def _run_stdout_progress_loop(
        self,
        process: subprocess.Popen,
        progress_hook: Callable,
        stop_check: Callable[[], bool] | None,
    ) -> ProgressLoopResult:
        current_file = None
        last_progress: dict = {}

        try:
            for raw_line in iter(process.stdout.readline, ''):
                if not raw_line:
                    break

                if stop_check and stop_check():
                    log.info("Stop/pause detected via stop_check, killing process forcefully")
                    self._kill_process(process, graceful=False)
                    return ProgressLoopResult(current_file, last_progress, stopped=True)

                line = raw_line.strip()
                if line.startswith(YTDLP_FINAL_PATH_MARKER):
                    self.final_output_path = line[len(YTDLP_FINAL_PATH_MARKER):]
                    log.info(f"Final output path: {self.final_output_path}")
                    continue
                current_file = self._emit_destination_progress(line, current_file, progress_hook)
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
            self._kill_process(process, graceful=False)
            raise hook_error

        return ProgressLoopResult(current_file, last_progress)

    def _join_thread(self, thread: threading.Thread | None, timeout: float) -> None:
        if thread:
            thread.join(timeout=timeout)

    def _wait_for_download_result(
        self,
        process: subprocess.Popen,
        stderr_output: list[str],
        stderr_thread: threading.Thread,
        monitor_thread: threading.Thread | None,
        stop_requested: threading.Event,
    ) -> Tuple[bool, str]:
        if stop_requested.is_set():
            self._join_thread(monitor_thread, THREAD_JOIN_SHORT_TIMEOUT_SEC)
            self._join_thread(stderr_thread, PROCESS_TERMINATE_WAIT_SEC)
            return False, MSG_PAUSED_BY_USER

        try:
            process.wait(timeout=YTDLP_DOWNLOAD_PROCESS_TIMEOUT_SEC)
        except subprocess.TimeoutExpired:
            log.warning("yt-dlp process timeout, killing...")
            self._kill_process(process)
            self._join_thread(stderr_thread, PROCESS_TERMINATE_WAIT_SEC)
            return False, "Download timeout"

        self._join_thread(monitor_thread, THREAD_JOIN_SHORT_TIMEOUT_SEC)
        if stop_requested.is_set():
            self._join_thread(stderr_thread, PROCESS_TERMINATE_WAIT_SEC)
            return False, MSG_PAUSED_BY_USER

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
    ) -> Tuple[bool, str]:
        """
        Download a video through the managed external yt-dlp executable.

        Args:
            url: Download URL.
            options: yt-dlp option dictionary.
            progress_hook: Progress callback.
            is_resume: Whether the task is being resumed.
            stop_check: Callback returning True when the process should stop.

        Returns:
            (success, error message)
        """
        process = None
        stderr_output: list[str] = []
        stop_requested = threading.Event()
        self.final_output_path = None

        try:
            args = self._build_command(url, options, is_resume)
            logged_args = [redact_url_for_log(arg) if arg == url else arg for arg in args]
            log.info(f"Running yt-dlp: {' '.join(logged_args)}")

            process = self._start_download_process(args)
            stderr_thread = self._start_stderr_drain(process, stderr_output)
            monitor_thread = self._start_stop_monitor(process, stop_check, stop_requested)

            progress_result = self._run_stdout_progress_loop(process, progress_hook, stop_check)
            if progress_result.stopped:
                self._join_thread(monitor_thread, THREAD_JOIN_SHORT_TIMEOUT_SEC)
                self._join_thread(stderr_thread, PROCESS_TERMINATE_WAIT_SEC)
                return False, MSG_PAUSED_BY_USER

            return self._wait_for_download_result(
                process,
                stderr_output,
                stderr_thread,
                monitor_thread,
                stop_requested,
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

    def extract_info(
        self,
        url: str,
        download: bool = False,
        options: Optional[Dict] = None,
    ) -> Tuple[Optional[Dict], bool]:
        """
        Extract metadata through the managed external yt-dlp executable.

        Args:
            url: YouTube URL.
            download: Whether to download. False means metadata only.
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

    def _convert_to_bytes(self, size: float, unit: str) -> int:
        """Convert a yt-dlp size string unit to bytes while preserving the existing API."""
        return convert_to_bytes(size, unit)

    def _parse_eta(self, eta_str: str) -> int:
        """Convert a yt-dlp ETA string to seconds while preserving the existing API."""
        return parse_eta(eta_str)

    def _build_command(self, url: str, options: Dict, is_resume: bool = False) -> List[str]:
        """Convert yt-dlp option dicts to CLI arguments while preserving the existing API."""
        return build_command(self.ytdlp_path, self.ffmpeg_path, url, options, is_resume)
