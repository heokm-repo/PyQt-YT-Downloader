import os
import sys
import unittest
from types import SimpleNamespace
from unittest.mock import Mock

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
SRC = os.path.join(ROOT, "src")
TEST_APPDATA = os.path.join(ROOT, "tests", ".appdata")
os.makedirs(TEST_APPDATA, exist_ok=True)
os.environ["APPDATA"] = TEST_APPDATA
if SRC not in sys.path:
    sys.path.insert(0, SRC)

from constants import TaskStatus
from gui.tasks.task_actions import TaskActions


class TaskActionsRetryTests(unittest.TestCase):
    def test_failed_task_is_requeued_as_resume_without_replacing_task(self):
        task = SimpleNamespace(
            id=7,
            status=TaskStatus.FAILED,
            url="https://example.invalid/video",
            settings={"format": "mp4"},
            meta={"id": "video-id"},
            output_path="",
        )
        widget = SimpleNamespace(
            set_status=Mock(),
            status_label=SimpleNamespace(setText=Mock()),
        )
        scheduler = SimpleNamespace(resume_task=Mock(), add_task=Mock())
        window = SimpleNamespace(
            toggle_enabled=True,
            settings={"format": "webm"},
            scheduler=scheduler,
            task_widgets={7: widget},
            get_task_by_id=Mock(return_value=task),
            update_progress_ui=Mock(),
            remove_task_from_list=Mock(),
            start_download=Mock(),
        )

        TaskActions(window).retry_task(7)

        scheduler.resume_task.assert_called_once_with(7)
        scheduler.add_task.assert_called_once_with(
            1,
            7,
            task.url,
            {"format": "mp4"},
            task.meta,
            is_resume=True,
        )
        self.assertEqual(task.status, TaskStatus.WAITING)
        window.remove_task_from_list.assert_not_called()
        window.start_download.assert_not_called()


if __name__ == "__main__":
    unittest.main()
