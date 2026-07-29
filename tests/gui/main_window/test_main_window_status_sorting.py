import os
import sys
import unittest
from types import SimpleNamespace

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
SRC = os.path.join(ROOT, "src")
TEST_APPDATA = os.path.join(ROOT, "tests", ".appdata")
os.makedirs(TEST_APPDATA, exist_ok=True)
os.environ["APPDATA"] = TEST_APPDATA
if SRC not in sys.path:
    sys.path.insert(0, SRC)

from constants import TaskStatus
from core.task_summary import summarize_task_progress
from data.models import DownloadTask
from gui.windows.main_window import (
    TASK_SORT_NEWEST,
    TASK_SORT_OLDEST,
    TASK_SORT_STATUS,
    YTDownloaderPyQt5,
)


class FakeSortButton:
    def __init__(self, sort_key):
        self.sort_key = sort_key

    def currentKey(self):
        return self.sort_key


class FakeLabel:
    def __init__(self):
        self.text = None

    def setText(self, text):
        self.text = text


class FakeSlider:
    def __init__(self):
        self.value = None

    def minimum(self):
        return 0

    def maximum(self):
        return 100

    def setValue(self, value):
        self.value = value


def make_task(task_id, status):
    return DownloadTask(
        id=task_id,
        url=f"https://example.invalid/{task_id}",
        status=status,
    )


def make_window(sort_key, tasks):
    return SimpleNamespace(
        task_sort_button=FakeSortButton(sort_key),
        _current_task_sort_key=lambda: sort_key,
        tasks=tasks,
        task_widgets={task.id: object() for task in tasks},
    )


class MainWindowStatusSortingTests(unittest.TestCase):
    def test_sorted_task_ids_use_newest_and_oldest_task_ids(self):
        tasks = [
            make_task(1, TaskStatus.WAITING),
            make_task(3, TaskStatus.WAITING),
            make_task(2, TaskStatus.WAITING),
        ]

        newest_window = make_window(TASK_SORT_NEWEST, tasks)
        oldest_window = make_window(TASK_SORT_OLDEST, tasks)

        self.assertEqual(YTDownloaderPyQt5._sorted_task_ids(newest_window), [3, 2, 1])
        self.assertEqual(YTDownloaderPyQt5._sorted_task_ids(oldest_window), [1, 2, 3])

    def test_sorted_task_ids_use_status_priority_then_newest(self):
        tasks = [
            make_task(1, TaskStatus.FINISHED),
            make_task(2, TaskStatus.WAITING),
            make_task(3, TaskStatus.FAILED),
            make_task(4, TaskStatus.DOWNLOADING),
            make_task(5, TaskStatus.PAUSED),
            make_task(6, TaskStatus.FAILED),
        ]
        window = make_window(TASK_SORT_STATUS, tasks)

        self.assertEqual(YTDownloaderPyQt5._sorted_task_ids(window), [6, 3, 4, 5, 2, 1])

    def test_task_counter_uses_finished_total_and_bar_uses_finished_ratio(self):
        tasks = [
            make_task(1, TaskStatus.WAITING),
            make_task(2, TaskStatus.DOWNLOADING),
            make_task(3, TaskStatus.PAUSED),
            make_task(4, TaskStatus.FINISHED),
            make_task(5, TaskStatus.FAILED),
        ]
        window = SimpleNamespace(
            task_counter_label=FakeLabel(),
            progress_slider=FakeSlider(),
            tasks=tasks,
        )

        YTDownloaderPyQt5._update_task_counter_ui(window, summarize_task_progress(tasks))

        self.assertEqual(window.task_counter_label.text, "1/5")
        self.assertEqual(window.progress_slider.value, 20)


if __name__ == "__main__":
    unittest.main()