"""Raw timing distributions and Windows native process memory."""

from __future__ import annotations

import ctypes
from ctypes import wintypes
import math
import statistics
import sys
import time


def distribution(values: list[float]) -> dict:
    ordered = sorted(values)
    return {"samples": values, "median": statistics.median(values),
            "p95": ordered[math.ceil(len(ordered) * 0.95) - 1],
            "min": ordered[0], "max": ordered[-1]}


def measure(operation, repeats: int, warmups: int = 1) -> dict:
    for _ in range(warmups):
        operation()
    samples, outcomes = [], []
    for _ in range(repeats):
        start = time.perf_counter()
        outcomes.append(operation())
        samples.append((time.perf_counter() - start) * 1000)
    return {"elapsed_ms": distribution(samples), "outcomes": outcomes, "warmups": warmups}


def process_memory() -> dict:
    if sys.platform != "win32":
        return {"available": False}

    class Counters(ctypes.Structure):
        _fields_ = [("cb", wintypes.DWORD), ("PageFaultCount", wintypes.DWORD)] + [
            (name, ctypes.c_size_t) for name in (
                "PeakWorkingSetSize", "WorkingSetSize", "QuotaPeakPagedPoolUsage",
                "QuotaPagedPoolUsage", "QuotaPeakNonPagedPoolUsage", "QuotaNonPagedPoolUsage",
                "PagefileUsage", "PeakPagefileUsage", "PrivateUsage",
            )
        ]

    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    psapi = ctypes.WinDLL("psapi", use_last_error=True)
    kernel.GetCurrentProcess.restype = wintypes.HANDLE
    psapi.GetProcessMemoryInfo.argtypes = [wintypes.HANDLE, ctypes.POINTER(Counters), wintypes.DWORD]
    psapi.GetProcessMemoryInfo.restype = wintypes.BOOL
    counters = Counters()
    counters.cb = ctypes.sizeof(counters)
    if not psapi.GetProcessMemoryInfo(kernel.GetCurrentProcess(), ctypes.byref(counters), counters.cb):
        raise ctypes.WinError(ctypes.get_last_error())
    return {"private_bytes": counters.PrivateUsage, "working_set_bytes": counters.WorkingSetSize,
            "peak_working_set_bytes": counters.PeakWorkingSetSize}
