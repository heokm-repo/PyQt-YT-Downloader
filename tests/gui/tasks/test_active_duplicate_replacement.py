import os
import sys
import unittest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
SRC = os.path.join(ROOT, "src")
if SRC not in sys.path:
    sys.path.insert(0, SRC)

from gui.tasks.active_duplicate_replacement import (
    DUPLICATE_STOP_POLL_MS,
    wait_for_task_stop,
)


class FakeScheduler:
    def __init__(self, running=True):
        self.running = running
        self.queries = []

    def is_task_running(self, task_id):
        self.queries.append(task_id)
        return self.running


class ActiveDuplicateReplacementTests(unittest.TestCase):
    def test_wait_is_scheduled_without_blocking_until_task_stops(self):
        scheduler = FakeScheduler(running=True)
        scheduled = []
        events = []

        wait_for_task_stop(
            scheduler,
            7,
            lambda delay, callback: scheduled.append((delay, callback)),
            lambda: events.append("stopped"),
            lambda: events.append("timeout"),
            attempts_left=2,
        )

        self.assertEqual(events, [])
        self.assertEqual(len(scheduled), 1)
        self.assertEqual(scheduled[0][0], DUPLICATE_STOP_POLL_MS)

        scheduler.running = False
        scheduled.pop()[1]()

        self.assertEqual(events, ["stopped"])
        self.assertEqual(scheduler.queries, [7, 7])

    def test_timeout_never_reports_stopped_or_starts_replacement(self):
        scheduler = FakeScheduler(running=True)
        scheduled = []
        events = []

        wait_for_task_stop(
            scheduler,
            9,
            lambda delay, callback: scheduled.append((delay, callback)),
            lambda: events.append("stopped"),
            lambda: events.append("timeout"),
            attempts_left=1,
        )
        scheduled.pop()[1]()

        self.assertEqual(events, ["timeout"])


if __name__ == "__main__":
    unittest.main()
