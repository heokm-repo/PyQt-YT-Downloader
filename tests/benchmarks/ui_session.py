"""Real Qt widgets with worker startup disabled for offline measurements."""

from __future__ import annotations

from contextlib import contextmanager
import gc
from pathlib import Path
from unittest.mock import patch


def create_application():
    # Keep the production WebEngine-before-QApplication import ordering.
    from PyQt5 import QtWebEngineWidgets  # noqa: F401
    from PyQt5.QtCore import Qt
    from PyQt5.QtWidgets import QApplication
    from gui.windowing.high_dpi import configure_qt_display_policy

    configure_qt_display_policy(QApplication, Qt)
    app = QApplication.instance() or QApplication([])
    app.setQuitOnLastWindowClosed(False)
    return app


def drain_deletions(app):
    from PyQt5.QtCore import QCoreApplication, QEvent

    QCoreApplication.sendPostedEvents(None, QEvent.DeferredDelete)
    app.processEvents()
    gc.collect()


@contextmanager
def offline_window(app, settings):
    from PyQt5.QtCore import Qt
    from gui.windows.main_window import YTDownloaderPyQt5

    # The real scheduler and registration queue remain; no workers can consume it.
    with patch.object(YTDownloaderPyQt5, "_initialize_scheduler"), \
            patch.object(YTDownloaderPyQt5, "load_tasks_from_file"):
        window = YTDownloaderPyQt5(initial_settings=settings)
    try:
        window.setAttribute(Qt.WA_DontShowOnScreen, True)
        window.show()
        app.processEvents()
        yield window
    finally:
        window.close()
        window.deleteLater()
        drain_deletions(app)


def capture_ui(app, output: Path, settings: dict) -> list[str]:
    from PyQt5.QtCore import Qt
    from constants import TaskStatus, change_language
    from gui.tasks.task_widget_restore import restore_task_widget_state
    from gui.windows.settings_dialog import SettingsDialog
    from .fixtures import task_records

    directory = output / "screenshots"
    directory.mkdir()
    captures = []

    def capture(widget, name):
        app.processEvents()
        path = directory / name
        if not widget.grab().save(str(path), "PNG"):
            raise RuntimeError(f"Could not capture {path}")
        captures.append(str(path.relative_to(output)))

    for theme in ("light", "dark"):
        current_settings = {**settings, "theme": theme}
        change_language("ko")
        with offline_window(app, current_settings) as window:
            capture(window, f"main-empty-{theme}.png")
            for record in task_records(5, current_settings):
                task = window._create_and_register_task(
                    record["id"], record["url"], record["video_id"], "youtube"
                )
                task.status = TaskStatus.from_string(record["status"])
                task.meta = record["meta"]
                restore_task_widget_state(window.task_widgets[task.id], task)
                window.task_widgets[task.id].set_status(task.status)
                if task.status == TaskStatus.DOWNLOADING:
                    window.task_widgets[task.id].set_started()
            window.task_sort_button.setCurrentKey("status")
            window._show_task_list()
            window.update_progress_ui()
            capture(window, f"main-tasks-{theme}.png")
            dialog = SettingsDialog(dict(current_settings), parent=window)
            dialog.setAttribute(Qt.WA_DontShowOnScreen, True)
            dialog.show()
            try:
                for index in range(dialog.tab_widget.count()):
                    dialog.tab_widget.setCurrentIndex(index)
                    capture(dialog, f"settings-{index + 1}-{theme}.png")
            finally:
                dialog.close()
                dialog.deleteLater()
    return captures
