"""Compare real HTTP thumbnail requests/cards against an optional source snapshot."""
import argparse
from contextlib import ExitStack
import os
from pathlib import Path
import sys
import time
from unittest.mock import patch

from .environment import ROOT, environment_manifest, file_manifest, prepare_run, write_json
from .fixtures import settings_fixture
from .measurements import distribution, process_memory


def spin_until(app, condition, timeout=15):
    from PyQt5.QtCore import QEventLoop
    from PyQt5.QtTest import QTest
    deadline = time.monotonic() + timeout
    while not condition():
        if time.monotonic() >= deadline:
            raise AssertionError('Thumbnail fixture timed out')
        app.processEvents(QEventLoop.AllEvents, 10)
        QTest.qWait(1)


def sample(app, settings, unique, screenshot=None):
    from PyQt5.QtNetwork import QNetworkAccessManager, QNetworkReply
    from PyQt5.QtGui import QPixmap
    from constants import TaskStatus
    from data.models import DownloadTask
    from gui.widgets import task_item
    from .thumbnail_server import ThumbnailServer
    from .ui_session import offline_window, drain_deletions

    server = ThumbnailServer()
    before = process_memory()
    try:
        with offline_window(app, settings) as window, ExitStack() as stack:
            shared = hasattr(window, 'thumbnail_loader')
            if shared:
                loader = window.thumbnail_loader
                decode = stack.enter_context(patch.object(loader, '_decode', wraps=loader._decode))
            else:
                decode = stack.enter_context(patch.object(task_item, 'QPixmap', wraps=QPixmap))
            start = time.perf_counter()
            with window.task_list.batch():
                for index in range(100):
                    url = f'http://127.0.0.1:{server.serverPort()}/{index % unique}.png'
                    metadata = {'thumbnail': url, 'title': f'썸네일 검증 {index}', 'uploader': 'Local fixture'}
                    if index < 50:
                        window._create_and_register_task(index + 1, 'offline')
                        window.task_widgets[index + 1].update_metadata(metadata)
                    else:
                        window.task_list.restore(DownloadTask(index + 1, 'offline', settings=settings,
                                                             status=TaskStatus.FINISHED, meta=metadata))
            # Qt limits a shared manager to six concurrent requests per host.
            # Keep responses held until those first requests have reached HTTP.
            spin_until(app, lambda: len(server.requests) >= (min(unique, 6) if shared else 100))
            pending = {'managers': len(window.findChildren(QNetworkAccessManager)),
                       'replies': len(window.findChildren(QNetworkReply)), 'memory': process_memory()}
            # Every mixed URL retains subscribers; in the unique fixture, half are cancelled.
            with window.task_list.batch():
                for task_id in range(1, 51):
                    window.remove_task_from_list(task_id, discard_workspace=False)
            drain_deletions(app)
            after_remove = len(window.findChildren(QNetworkReply))
            server.release()
            spin_until(app, lambda: all(w.thumb_label.pixmap() is not None and
                                       not w.thumb_label.pixmap().isNull()
                                       for w in window.task_widgets.values()))
            elapsed = (time.perf_counter() - start) * 1000
            # Independent legacy decode/scale oracle; every card must show the same image.
            from PyQt5.QtCore import Qt
            expected = QPixmap()
            assert expected.loadFromData(server.body)
            expected = expected.scaled(160, 90, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
            assert all(w.thumb_label.pixmap().toImage() == expected.toImage()
                       for w in window.task_widgets.values())
            assert decode.call_count == (min(unique, 50) if shared else 50)
            drain_deletions(app)
            completed_memory = process_memory()
            assert not window.findChildren(QNetworkReply)
            if shared:
                assert not loader._subscriptions and not loader._requests and not loader._owners
            if screenshot is not None:
                window._show_task_list()
                app.processEvents()
                assert window.grab().save(str(screenshot), 'PNG')
            result = {'elapsed_ms': elapsed, 'actual_requests': len(server.requests),
                      'payload_bytes': server.payload_bytes, 'decode_count': decode.call_count,
                      'pending': pending, 'replies_after_removal': after_remove,
                      'replies_after_completion': 0, 'memory_before': before,
                      'memory_completed': completed_memory}
        result['memory_after_window_deletion'] = process_memory()
        return result
    finally:
        server.dispose()
        drain_deletions(app)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--source', type=Path, default=ROOT / 'src')
    parser.add_argument('--repeats', type=int, default=20)
    parser.add_argument('--scale', choices=('1', '1.5', '2'), default='1')
    args = parser.parse_args()
    if args.repeats < 1:
        parser.error('--repeats must be positive')
    output = prepare_run(args.output, qt_platform='windows')
    source = args.source.resolve()
    sys.path.insert(0, str(source))
    os.environ['QT_SCALE_FACTOR'] = args.scale
    manifest = environment_manifest()
    manifest['measured_source'] = str(source)
    manifest['measured_source_files'] = file_manifest(source, suffixes={'.py'})
    write_json(output / 'environment.json', manifest)
    settings = settings_fixture(output / 'downloads')
    from .ui_session import create_application
    app = create_application()
    results = {'repeats': args.repeats, 'warmups': 1,
               'qt': {'platform': app.platformName(), 'dpr': app.primaryScreen().devicePixelRatio()},
               'limitations': ['Loopback HTTP only; no external hosts, workers or installer',
                               '100 cards: 50 new, 50 restored; first 50 deleted while loading',
                               'Native memory points include Qt/OS caches; not a leak proof',
                               'No completed cache or scaled decoder enabled'], 'cases': []}
    for unique in (10, 100):
        sample(app, settings, unique)
        samples = []
        for iteration in range(args.repeats):
            samples.append(sample(app, settings, unique,
                                  output / f'thumbnails-{unique}.png' if iteration == 0 else None))
            print(f'Thumbnails unique={unique} sample={iteration + 1}/{args.repeats}', flush=True)
        results['cases'].append({'cards': 100, 'unique_urls': unique, 'samples': samples,
                                 'elapsed_ms': distribution([s['elapsed_ms'] for s in samples])})
        write_json(output / 'results.json', results)
    app.quit()


if __name__ == '__main__':
    main()
