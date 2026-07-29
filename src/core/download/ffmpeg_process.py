"""Shared cancellable execution for managed FFmpeg post-processing."""

from __future__ import annotations

from dataclasses import dataclass
import os
import subprocess
import threading
import time
from typing import Any, Callable, Sequence

from constants import (
    DEFAULT_ENCODING,
    PROCESS_MONITOR_INTERVAL_SEC,
    PROCESS_TERMINATE_WAIT_SEC,
)
from utils.logger import log


@dataclass(frozen=True)
class FfmpegExecutionResult:
    success: bool
    error: str = ""
    paused: bool = False
    process_stopped: bool = True


def _drain_stderr(stream: Any, output: list[str]) -> None:
    try:
        for line in iter(stream.readline, ""):
            if line:
                output.append(line)
    except (OSError, ValueError):
        return


def _stop_process(process: subprocess.Popen | None) -> bool:
    if not process or process.poll() is not None:
        return True
    try:
        process.kill()
    except OSError as exc:
        log.debug("FFmpeg process kill failed: %s", exc)
    try:
        process.wait(timeout=PROCESS_TERMINATE_WAIT_SEC)
    except subprocess.TimeoutExpired:
        return process.poll() is not None
    except (OSError, subprocess.SubprocessError):
        return process.poll() is not None
    return process.poll() is not None


def run_ffmpeg_command(
    command: Sequence[str],
    *,
    stop_check: Callable[[], bool] | None,
    timeout_sec: float,
    timeout_error: str,
) -> FfmpegExecutionResult:
    """Run FFmpeg while honoring cancellation and a bounded processing timeout."""
    process = None
    stderr_thread = None
    stderr_output: list[str] = []
    started_at = time.monotonic()

    try:
        if stop_check and stop_check():
            return FfmpegExecutionResult(False, paused=True)

        process = subprocess.Popen(
            list(command),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            text=True,
            encoding=DEFAULT_ENCODING,
            errors="replace",
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
        )
        stderr_thread = threading.Thread(
            target=_drain_stderr,
            args=(process.stderr, stderr_output),
            daemon=True,
        )
        stderr_thread.start()

        while process.poll() is None:
            if stop_check and stop_check():
                process_stopped = _stop_process(process)
                if not process_stopped:
                    return FfmpegExecutionResult(
                        False,
                        "FFmpeg could not be stopped after cancellation",
                        process_stopped=False,
                    )
                return FfmpegExecutionResult(False, paused=True)
            if time.monotonic() - started_at > timeout_sec:
                process_stopped = _stop_process(process)
                return FfmpegExecutionResult(
                    False,
                    timeout_error,
                    process_stopped=process_stopped,
                )
            time.sleep(PROCESS_MONITOR_INTERVAL_SEC)

        stderr_thread.join(timeout=1)
        stderr = "".join(stderr_output).strip()
        if process.returncode != 0:
            error = (
                stderr.splitlines()[-1]
                if stderr
                else f"FFmpeg exited with code {process.returncode}"
            )
            return FfmpegExecutionResult(False, error)
        return FfmpegExecutionResult(True)
    except Exception as exc:
        process_stopped = _stop_process(process)
        return FfmpegExecutionResult(
            False,
            str(exc),
            process_stopped=process_stopped,
        )
    finally:
        if stderr_thread:
            stderr_thread.join(timeout=1)
