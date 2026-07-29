"""Build and launch a detached command for restarting the application."""

from __future__ import annotations

from dataclasses import dataclass
import os
import sys
from typing import Callable, Sequence


RESTART_WAIT_PID_ARG = "--restart-wait-pid"
RESTART_WAIT_TIMEOUT_MS = 30_000


@dataclass(frozen=True)
class RestartCommand:
    """Executable, arguments, and working directory used for a restart."""

    program: str
    arguments: tuple[str, ...]
    working_directory: str


def split_restart_wait_argument(argv: Sequence[str]) -> tuple[list[str], int | None]:
    """Remove the internal restart argument and return its process ID."""
    cleaned: list[str] = []
    wait_pid: int | None = None
    index = 0
    while index < len(argv):
        argument = argv[index]
        if argument == RESTART_WAIT_PID_ARG and index + 1 < len(argv):
            try:
                wait_pid = int(argv[index + 1])
            except (TypeError, ValueError):
                cleaned.extend((argument, argv[index + 1]))
            index += 2
            continue
        cleaned.append(argument)
        index += 1
    return cleaned, wait_pid


def build_restart_command(
    *,
    executable: str | None = None,
    argv: Sequence[str] | None = None,
    working_directory: str | None = None,
    is_frozen: bool | None = None,
    parent_pid: int | None = None,
) -> RestartCommand:
    """Return the correct restart command for packaged and source runs."""
    program = executable or sys.executable
    source_argv, _ = split_restart_wait_argument(
        list(argv if argv is not None else sys.argv)
    )
    frozen = getattr(sys, "frozen", False) if is_frozen is None else is_frozen

    if frozen:
        arguments = source_argv[1:]
    else:
        script_path = os.path.abspath(source_argv[0]) if source_argv else ""
        arguments = [script_path, *source_argv[1:]]

    arguments.extend(
        (RESTART_WAIT_PID_ARG, str(parent_pid or os.getpid()))
    )
    return RestartCommand(
        program=program,
        arguments=tuple(arguments),
        working_directory=working_directory or os.getcwd(),
    )


def launch_restart(
    command: RestartCommand | None = None,
    starter: Callable[[str, list[str], str], object] | None = None,
) -> bool:
    """Start the replacement process and normalize Qt's return value."""
    restart_command = command or build_restart_command()
    if starter is None:
        from PyQt5.QtCore import QProcess

        starter = QProcess.startDetached

    result = starter(
        restart_command.program,
        list(restart_command.arguments),
        restart_command.working_directory,
    )
    if isinstance(result, tuple):
        return bool(result[0])
    return bool(result)


def _wait_for_windows_process(process_id: int, timeout_ms: int) -> bool:
    """Wait for a Windows process handle without polling."""
    import ctypes
    from ctypes import wintypes

    synchronize = 0x00100000
    wait_timeout = 0x00000102
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel32.OpenProcess.argtypes = (
        wintypes.DWORD,
        wintypes.BOOL,
        wintypes.DWORD,
    )
    kernel32.OpenProcess.restype = wintypes.HANDLE
    kernel32.WaitForSingleObject.argtypes = (wintypes.HANDLE, wintypes.DWORD)
    kernel32.WaitForSingleObject.restype = wintypes.DWORD
    kernel32.CloseHandle.argtypes = (wintypes.HANDLE,)
    kernel32.CloseHandle.restype = wintypes.BOOL

    process_handle = kernel32.OpenProcess(synchronize, False, process_id)
    if not process_handle:
        return True
    try:
        return kernel32.WaitForSingleObject(process_handle, timeout_ms) != wait_timeout
    finally:
        kernel32.CloseHandle(process_handle)


def wait_for_restart_parent(
    argv: list[str] | None = None,
    *,
    timeout_ms: int = RESTART_WAIT_TIMEOUT_MS,
    waiter: Callable[[int, int], bool] | None = None,
) -> bool:
    """Consume the internal argument and wait until the old app has exited."""
    target_argv = argv if argv is not None else sys.argv
    cleaned, process_id = split_restart_wait_argument(target_argv)
    target_argv[:] = cleaned
    if process_id is None or process_id == os.getpid():
        return True
    if waiter is not None:
        return waiter(process_id, timeout_ms)
    if sys.platform != "win32":
        return True
    return _wait_for_windows_process(process_id, timeout_ms)
