import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(__file__))
SRC = os.path.join(ROOT, "src")
TEST_APPDATA = os.path.join(ROOT, "tests", ".appdata")
os.makedirs(TEST_APPDATA, exist_ok=True)
os.environ["APPDATA"] = TEST_APPDATA
if SRC not in sys.path:
    sys.path.insert(0, SRC)

from gui.main_window.worker_lifecycle import WorkerStopStatus, stop_running_worker


class FakeWorker:
    def __init__(self, running=True, wait_result=True):
        self.running = running
        self.wait_result = wait_result
        self.terminated = False
        self.wait_timeout = None

    def isRunning(self):
        return self.running

    def terminate(self):
        self.terminated = True

    def wait(self, timeout):
        self.wait_timeout = timeout
        return self.wait_result


class WorkerLifecycleTests(unittest.TestCase):
    def test_stop_running_worker_skips_missing_worker(self):
        result = stop_running_worker(None, 1000)

        self.assertEqual(result.status, WorkerStopStatus.NOT_RUNNING)
        self.assertFalse(result.timed_out)

    def test_stop_running_worker_skips_stopped_worker(self):
        worker = FakeWorker(running=False)

        result = stop_running_worker(worker, 1000)

        self.assertEqual(result.status, WorkerStopStatus.NOT_RUNNING)
        self.assertFalse(worker.terminated)
        self.assertIsNone(worker.wait_timeout)

    def test_stop_running_worker_terminates_and_waits(self):
        worker = FakeWorker(wait_result=True)

        result = stop_running_worker(worker, 1500)

        self.assertEqual(result.status, WorkerStopStatus.STOPPED)
        self.assertTrue(worker.terminated)
        self.assertEqual(worker.wait_timeout, 1500)

    def test_stop_running_worker_reports_timeout(self):
        worker = FakeWorker(wait_result=False)

        result = stop_running_worker(worker, 2000)

        self.assertEqual(result.status, WorkerStopStatus.TIMED_OUT)
        self.assertTrue(result.timed_out)


if __name__ == "__main__":
    unittest.main()