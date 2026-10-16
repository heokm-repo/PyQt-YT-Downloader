"""M1 import timings in fresh interpreters, separate from GUI/startup latency."""

import json
import subprocess
import sys
import time

from .environment import ROOT
from .measurements import distribution


IMPORT_SEQUENCES = (
        ("utils.utils", "utils.logger", "utils.bin.storage", "utils.bin.manager"),
        ("utils.bin.manager", "utils.bin.storage", "utils.logger", "utils.utils"),
        ("gui.windows.main_window",),
)


def import_sample(source_root, modules) -> tuple[float, float]:
    source = (
            "import importlib,json,sys,time; "
            "sys.path.insert(0,sys.argv[1]); start=time.perf_counter(); "
            "[importlib.import_module(name) for name in sys.argv[2:]]; "
            "print(json.dumps({'import_ms':(time.perf_counter()-start)*1000}))"
    )
    start = time.perf_counter()
    completed = subprocess.run(
        [sys.executable, "-B", "-c", source, str(source_root), *modules],
        capture_output=True, encoding="utf-8", check=True, timeout=60,
    )
    return json.loads(completed.stdout)["import_ms"], (time.perf_counter() - start) * 1000


def benchmark_imports(repeats: int) -> list[dict]:
    results = []
    for modules in IMPORT_SEQUENCES:
        elapsed, wall = [], []
        for iteration in range(repeats + 1):
            import_ms, wall_ms = import_sample(ROOT / "src", modules)
            if iteration:
                wall.append(wall_ms)
                elapsed.append(import_ms)
        results.append({"modules": modules, "import_ms": distribution(elapsed),
                        "process_wall_ms": distribution(wall), "warmups": 1})
    return results
