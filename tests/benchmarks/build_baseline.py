"""Build an unchanged source snapshot without touching existing dist/output."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

from .environment import ROOT, environment_manifest, file_manifest, prepare_run, write_json
from .fixtures import settings_fixture
from build_scripts.release_inputs import snapshot_inputs


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--frozen-smoke", action="store_true",
                        help="Build a separate instrumented variant and run an offline, hidden Qt smoke")
    args = parser.parse_args()
    output = prepare_run(args.output)
    snapshot = output / "snapshot"
    snapshot_inputs(ROOT, snapshot)
    if args.frozen_smoke:
        hook = snapshot / "frozen_smoke_hook.py"
        shutil.copy2(Path(__file__).with_name(hook.name), hook)
        spec = snapshot / "YTDownloader.spec"
        source = spec.read_text(encoding="utf-8")
        if source.count("runtime_hooks=[],") != 1:
            raise RuntimeError("Unexpected spec runtime hook boundary; inspect before instrumenting")
        spec.write_text(source.replace("runtime_hooks=[],", "runtime_hooks=['frozen_smoke_hook.py'],"),
                        encoding="utf-8")
    manifest = {"environment": environment_manifest(), "snapshot": file_manifest(snapshot),
                "kind": "instrumented-frozen-smoke" if args.frozen_smoke else "unchanged-baseline",
                "isolation": "Fresh source, AppData, temp, PyInstaller cache and output directories; "
                             "uses the recorded host Python packages, not a clean VM/venv",
                "installer": "not built or executed", "frozen_smoke": "not executed"}
    write_json(output / "manifest.json", manifest)
    env = {**os.environ, "PYINSTALLER_CONFIG_DIR": str(output / "pyinstaller-cache")}
    command = [sys.executable, "-B", "-m", "PyInstaller", "--noconfirm",
               "--distpath", str(output / "dist"), "--workpath", str(output / "work"),
               str(snapshot / "YTDownloader.spec")]
    start = time.perf_counter()
    with (output / "build.log").open("w", encoding="utf-8") as log:
        completed = subprocess.run(command, cwd=snapshot, env=env, stdout=log, stderr=subprocess.STDOUT)
    manifest.update(command=command, exit_code=completed.returncode,
                    build_seconds=time.perf_counter() - start)
    executable = output / "dist" / "YTDownloader" / "YTDownloader.exe"
    if completed.returncode == 0 and executable.is_file():
        manifest["artifacts"] = file_manifest(executable.parent)
        manifest["artifact_bytes"] = sum(item["bytes"] for item in manifest["artifacts"])
        manifest["artifact_files"] = len(manifest["artifacts"])
    write_json(output / "manifest.json", manifest)
    if completed.returncode:
        raise SystemExit(completed.returncode)
    if not executable.is_file():
        raise RuntimeError("PyInstaller returned success without the expected executable")
    if args.frozen_smoke:
        write_json(output / "appdata" / "YTDownloader" / "settings.json",
                   settings_fixture(output / "downloads"))
        smoke_env = {**env, "QT_QPA_PLATFORM": "windows", "YT_BENCHMARK_SMOKE_ROOT": str(output)}
        startup = subprocess.STARTUPINFO()
        startup.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startup.wShowWindow = 0  # Hide this diagnostic process.
        with (output / "smoke.log").open("w", encoding="utf-8") as log:
            completed = subprocess.run([str(executable)], cwd=executable.parent, env=smoke_env,
                                       stdout=log, stderr=subprocess.STDOUT,
                                       startupinfo=startup, timeout=60)
        result_path = output / "smoke-result.json"
        smoke = json.loads(result_path.read_text(encoding="utf-8")) if result_path.exists() else {}
        manifest["frozen_smoke"] = {"exit_code": completed.returncode, **smoke}
        write_json(output / "manifest.json", manifest)
        if completed.returncode != 0 or not smoke.get("success"):
            raise RuntimeError(f"Frozen smoke failed; inspect {output}")
    print(f"Baseline: {executable}\nManifest: {output / 'manifest.json'}")


if __name__ == "__main__":
    main()
