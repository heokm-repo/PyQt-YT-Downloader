"""Capture all locales/themes at one real Qt scale for preserved/current comparison."""
import argparse
import os
from pathlib import Path
import sys

from .environment import ROOT, environment_manifest, file_manifest, prepare_run, write_json
from .fixtures import settings_fixture


def capture_matrix(app, output, settings):
    from PyQt5.QtCore import QEvent, Qt
    from PyQt5.QtWidgets import QLabel, QPushButton, QToolButton, QCheckBox
    import locales
    from constants import TaskStatus
    from gui.windows.settings_dialog import SettingsDialog
    from .ui_session import offline_window, drain_deletions
    directory = output / 'screenshots'
    directory.mkdir()
    records = []

    def capture(widget, filename):
        app.processEvents()
        assert widget.grab().save(str(directory / filename), 'PNG')

    for language in locales.SUPPORTED_LANGUAGES:
        for theme in ('light', 'dark'):
            current = {**settings, 'language': language, 'theme': theme}
            prefix = f'{language}-{theme}'
            with offline_window(app, current) as window:
                with window.task_list.batch():
                    for task_id, status in enumerate((TaskStatus.FINISHED, TaskStatus.PAUSED,
                            TaskStatus.DOWNLOADING, TaskStatus.FAILED, TaskStatus.WAITING), 1):
                        window._create_and_register_task(task_id, 'UTF-8 — a long video title ' * 6)
                        window.task_widgets[task_id].set_status(status)
                window._show_task_list()
                window.task_sort_button.setCurrentKey('oldest')
                window._apply_task_sort_order()
                drain_deletions(app)
                capture(window, prefix + '-cards.png')
                card = window.task_widgets[1]
                card.selected = True
                button = card.btn_layout.itemAt(0).widget()
                button.setAttribute(Qt.WA_UnderMouse, True)
                app.sendEvent(button, QEvent(QEvent.Enter))
                capture(window, prefix + '-hover-selected.png')
                button.setAttribute(Qt.WA_UnderMouse, False)
                app.sendEvent(button, QEvent(QEvent.Leave))
                button.setEnabled(False)
                capture(window, prefix + '-disabled.png')
                dialog = SettingsDialog(dict(current), parent=window)
                dialog.folder_line.setText('C:/Benchmark/Downloads')  # Identical visible fixture path.
                dialog.setAttribute(Qt.WA_DontShowOnScreen, True)
                dialog.show()
                clips = []
                for tab in range(3):
                    dialog.tab_widget.setCurrentIndex(tab)
                    app.processEvents()
                    for widget in dialog.findChildren((QLabel, QPushButton, QToolButton, QCheckBox)):
                        if widget.isVisible() and widget.text():
                            width = widget.fontMetrics().horizontalAdvance(widget.text())
                            if width > widget.contentsRect().width():
                                clips.append({'tab': tab, 'text': widget.text(), 'text_width': width,
                                              'available': widget.contentsRect().width()})
                    capture(dialog, prefix + f'-settings-{tab}.png')
                dialog.reject()
                dialog.deleteLater()
                records.append({'language': language, 'theme': theme, 'clipping': clips})
            print(f'UI matrix {prefix}', flush=True)
    return records


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--source', type=Path, default=ROOT / 'src')
    parser.add_argument('--scale', choices=('1', '1.5', '2'), default='1')
    args = parser.parse_args()
    output = prepare_run(args.output, qt_platform='windows')
    os.environ['QT_SCALE_FACTOR'] = args.scale
    source = args.source.resolve()
    sys.path.insert(0, str(source))
    manifest = environment_manifest()
    manifest.update(measured_source=str(source), measured_source_files=file_manifest(source, suffixes={'.py'}))
    write_json(output / 'environment.json', manifest)
    from .ui_session import create_application
    app = create_application()
    records = capture_matrix(app, output, settings_fixture(output / 'downloads'))
    write_json(output / 'results.json', {'dpr': app.primaryScreen().devicePixelRatio(), 'cases': records})
    app.quit()


if __name__ == '__main__':
    main()
