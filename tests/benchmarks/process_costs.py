"""Synthetic output/scan costs; no external network or media execution."""
import argparse
import sys
import time
import tracemalloc
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from .environment import ROOT, prepare_run, environment_manifest, file_manifest, write_json
from .measurements import distribution
from .worker_lifetime import run_worker_probes


def output_probes():
    from core.download import ffmpeg_process
    from core.ytdlp.wrapper import YtDlpWrapper
    results = {}
    for size in (1000, 100000):
        class Stream:
            remaining = size

            def readline(self):
                if not self.remaining:
                    return ''
                self.remaining -= 1
                return f'{self.remaining:08d} ' + 'x' * 240 + '\n'

        tracemalloc.start()
        output = ffmpeg_process.LastErrorLine() if hasattr(ffmpeg_process, 'LastErrorLine') else []
        ffmpeg_process._drain_stderr(Stream(), output)
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        results[f'ffmpeg_{size}'] = {'python_retained_bytes': current, 'python_peak_bytes': peak}

    produced = consumed = high_water = 0
    count = 100000

    class Stdout:
        def readline(self):
            nonlocal produced, high_water
            if produced == count:
                return ''
            produced += 1
            high_water = max(high_water, produced - consumed)
            return f'fixture line {produced}\n'

    wrapper = YtDlpWrapper('unused')

    def consume(line, current_file, last_progress, hook):
        nonlocal consumed
        consumed += 1
        if consumed % 100 == 0:
            time.sleep(0.001)
        return last_progress

    start = time.perf_counter()
    with patch.object(wrapper, '_emit_download_progress', side_effect=consume):
        wrapper._run_stdout_progress_loop(SimpleNamespace(stdout=Stdout()), lambda _: None, None)
    results['stdout_slow_consumer'] = {'lines': consumed, 'max_outstanding_lines': high_water,
                                       'elapsed_ms': (time.perf_counter()-start)*1000}
    return results


def scan_probes(output):
    from core.ytdlp.process_watchdog import ProcessWatchdog
    import os
    results = {}
    for count in (0, 100, 1000):
        directory = output / f'files-{count}'
        directory.mkdir()
        for i in range(count):
            (directory / str(i)).write_bytes(b'x')
        original = os.stat
        timings, calls = [], []
        for _ in range(21):
            start = time.perf_counter()
            ProcessWatchdog._directory_snapshot(str(directory))
            elapsed = (time.perf_counter()-start)*1000
            with patch('core.ytdlp.process_watchdog.os.stat', wraps=original) as stat:
                ProcessWatchdog._directory_snapshot(str(directory))
                calls.append(stat.call_count)
                timings.append(elapsed)
        results[str(count)] = {'ms': distribution(timings[1:]), 'stat_calls': calls[1:]}
        watchdog = ProcessWatchdog(SimpleNamespace(poll=lambda: None), None, lambda _: None, 60, .1)
        watchdog.watch_output_directory(str(directory))

        def poll():
            if hasattr(watchdog, '_poll_output_activity'):
                watchdog._poll_output_activity()
            else:
                watchdog._poll_file_activity()
                watchdog._poll_directory_activity()

        for mode in ('active', 'quiet'):
            timings = []
            for _ in range(21):
                watchdog.notify_activity()
                now = time.monotonic() + (2 if mode == 'quiet' else 0)
                with patch('core.ytdlp.process_watchdog.time.monotonic', return_value=now):
                    start = time.perf_counter()
                    poll()
                    timings.append((time.perf_counter()-start)*1000)
            watchdog.notify_activity()
            now = time.monotonic() + (2 if mode == 'quiet' else 0)
            with patch('core.ytdlp.process_watchdog.time.monotonic', return_value=now), patch(
                'core.ytdlp.process_watchdog.os.stat', wraps=original
            ) as stat:
                poll()
                results[str(count)][mode] = {'ms': distribution(timings[1:]), 'stat_calls': stat.call_count}
    return results


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--source', type=Path, default=ROOT/'src')
    args = parser.parse_args()
    output = prepare_run(args.output)
    sys.path.insert(0, str(args.source.resolve()))
    write_json(output/'environment.json', environment_manifest())
    from PyQt5.QtWidgets import QApplication
    app = QApplication([])
    results = {'source': str(args.source.resolve()), 'source_files': file_manifest(args.source, suffixes={'.py'}),
               'workers': run_worker_probes(app), 'output': output_probes(), 'scans': scan_probes(output)}
    write_json(output/'results.json', results)
    print(output/'results.json')


if __name__ == '__main__':
    main()
