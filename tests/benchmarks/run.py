"""Run offline S0 fixtures and measurements (not part of normal pytest)."""

from __future__ import annotations

import argparse
from pathlib import Path

from .environment import environment_manifest, prepare_run, write_json
from .fixtures import FIXTURE_VERSION, HISTORY_SIZES, LIST_SIZES, settings_fixture, task_records


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True,
                        help="New directory below build/benchmarks; existing directories are refused")
    parser.add_argument("--groups", nargs="+", choices=("imports", "duplicates", "lookup", "lists", "capture"),
                        default=["imports", "duplicates", "lists", "capture"])
    parser.add_argument("--repeats", type=int, default=20)
    parser.add_argument("--qt-platform", choices=("offscreen", "windows"), default="offscreen")
    parser.add_argument("--list-sizes", nargs="+", type=int, choices=LIST_SIZES, default=list(LIST_SIZES))
    parser.add_argument("--history-sizes", nargs="+", type=int, choices=HISTORY_SIZES,
                        default=list(HISTORY_SIZES))
    args = parser.parse_args()
    if args.repeats < 1:
        parser.error("--repeats must be positive")
    output = prepare_run(args.output, qt_platform=args.qt_platform)
    settings = settings_fixture(output / "downloads")
    write_json(output / "appdata" / "YTDownloader" / "settings.json", settings)
    write_json(output / "fixtures" / "settings.json", settings)
    write_json(output / "fixtures" / "tasks.json", task_records(1000, settings))
    write_json(output / "environment.json", environment_manifest())
    results = {
        "fixture_version": FIXTURE_VERSION, "repeats": args.repeats,
        "timing_grade": "baseline" if args.repeats >= 20 else "smoke-only",
        "limitations": ["Hidden widget rendering at QT_SCALE_FACTOR=1; not interactive desktop QA",
                        "No network, worker execution, login, media download or installer execution",
                        "Instrumentation overhead is included; compare with the same harness",
                        "Native memory is sampled, not a continuous peak/leak measurement"],
    }
    if "imports" in args.groups:
        from .imports import benchmark_imports
        results["imports"] = benchmark_imports(args.repeats)
        write_json(output / "results.json", results)
    if "duplicates" in args.groups:
        from .duplicates import benchmark_duplicates
        results["duplicates"] = benchmark_duplicates(output, settings, args.repeats, args.history_sizes)
        write_json(output / "results.json", results)
    if "lookup" in args.groups:
        from .task_lookup import benchmark_task_lookup
        results["lookup"] = benchmark_task_lookup(settings, args.repeats)
        write_json(output / "results.json", results)
    if "lists" in args.groups or "capture" in args.groups:
        from .ui_session import capture_ui, create_application
        app = create_application()
        results["qt"] = {"platform": app.platformName(), "font": app.font().family(),
                         "screen_dpr": app.primaryScreen().devicePixelRatio(),
                         "logical_dpi": app.primaryScreen().logicalDotsPerInch()}
        if "lists" in args.groups:
            from .task_list import benchmark_lists
            results["lists"] = benchmark_lists(app, settings, args.list_sizes, args.repeats)
            write_json(output / "results.json", results)
        if "capture" in args.groups:
            results["screenshots"] = capture_ui(app, output, settings)
        app.quit()
    write_json(output / "results.json", results)
    print(f"Results: {output / 'results.json'}", flush=True)


if __name__ == "__main__":
    main()
