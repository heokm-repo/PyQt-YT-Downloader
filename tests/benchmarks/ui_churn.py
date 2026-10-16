"""M5: button allocation and native memory during repeated card updates."""
import argparse
from collections import Counter
from pathlib import Path
import sys
import time
from unittest.mock import patch

from .environment import ROOT, environment_manifest, file_manifest, prepare_run, write_json
from .fixtures import settings_fixture
from .measurements import distribution, process_memory


def sample(app, settings, mode):
    from PyQt5.QtWidgets import QPushButton
    from constants import TaskStatus
    from gui.theme import apply_application_theme
    from gui.widgets.task_item import TaskWidget
    from .ui_session import offline_window, drain_deletions
    counts = Counter()
    create = TaskWidget.create_action_button

    def created(widget, *args, **kwargs):
        button = create(widget, *args, **kwargs)
        counts['created'] += 1
        button.destroyed.connect(lambda: counts.update(['destroyed']))
        return button

    with patch.object(TaskWidget, 'create_action_button', created):
        with offline_window(app, settings) as window:
            with window.task_list.batch():
                for task_id in range(1, 21):
                    window._create_and_register_task(task_id, 'offline')
            cards = list(window.task_widgets.values())
            for card in cards:
                card.set_status(TaskStatus.FINISHED)
            drain_deletions(app)
            counts.clear()
            before = process_memory()
            start = time.perf_counter()
            for cycle in range(20):
                if mode == 'same_status':
                    for _ in range(5):
                        for card in cards:
                            card.set_status(TaskStatus.FINISHED)
                elif mode == 'transitions':
                    for status in (TaskStatus.WAITING, TaskStatus.PAUSED, TaskStatus.DOWNLOADING,
                                   TaskStatus.FINISHED, TaskStatus.FAILED):
                        for card in cards:
                            card.set_status(status)
                else:
                    apply_application_theme('dark' if cycle % 2 == 0 else 'light')
                    for card in cards:
                        card.selected = bool(cycle % 2)
                        card.apply_theme()
                # Match a GUI turn between command batches, including deferred deletion.
                drain_deletions(app)
            elapsed = (time.perf_counter() - start) * 1000
            expected = 2 if mode == 'transitions' else 4
            assert all(c.btn_layout.count() == expected for c in cards)
            assert all(len(c.btn_container.findChildren(QPushButton)) == expected for c in cards)
            result = {'elapsed_ms': elapsed, 'calls': dict(counts), 'live_buttons': expected * 20,
                      'memory_before': before, 'memory_completed': process_memory()}
        result['memory_after_deletion'] = process_memory()
        # Include the original 80 buttons present when measurement started.
        assert counts['destroyed'] == counts['created'] + 80
        result['calls_after_window_deletion'] = dict(counts)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--source', type=Path, default=ROOT / 'src')
    parser.add_argument('--repeats', type=int, default=20)
    args = parser.parse_args()
    if args.repeats < 1:
        parser.error('--repeats must be positive')
    output = prepare_run(args.output, qt_platform='windows')
    source = args.source.resolve()
    sys.path.insert(0, str(source))
    manifest = environment_manifest()
    manifest.update(measured_source=str(source), measured_source_files=file_manifest(source, suffixes={'.py'}))
    write_json(output / 'environment.json', manifest)
    from .ui_session import create_application
    app = create_application()
    settings = settings_fixture(output / 'downloads')
    results = {'warmups': 1, 'repeats': args.repeats, 'cards': 20, 'cycles': 20, 'cases': []}
    for mode in ('same_status', 'transitions', 'theme_selection'):
        sample(app, settings, mode)
        samples = []
        for index in range(args.repeats):
            samples.append(sample(app, settings, mode))
            print(f'UI {mode} sample={index + 1}/{args.repeats}', flush=True)
        results['cases'].append({'mode': mode, 'samples': samples,
                                 'elapsed_ms': distribution([s['elapsed_ms'] for s in samples])})
        write_json(output / 'results.json', results)
    app.quit()


if __name__ == '__main__':
    main()
