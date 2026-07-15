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

from core.ytdlp.wrapper import YtDlpWrapper, _ytdlp_environment


class FakeStdout:
    def __init__(self, lines):
        self.lines = list(lines)

    def readline(self):
        if not self.lines:
            return ""
        return self.lines.pop(0)


class FakeProcess:
    def __init__(self, lines):
        self.stdout = FakeStdout(lines)
        self.killed = False

    def poll(self):
        return None


class YtDlpWrapperLifecycleTests(unittest.TestCase):
    def test_ytdlp_environment_disables_plugin_loading(self):
        self.assertEqual(_ytdlp_environment()["YTDLP_NO_PLUGINS"], "1")
        self.assertEqual(_ytdlp_environment()["PYTHONIOENCODING"], "utf-8")

    def test_stdout_progress_loop_tracks_current_file_and_completion(self):
        wrapper = YtDlpWrapper("yt-dlp.exe")
        events = []
        process = FakeProcess(
            [
                "[download] Destination: sample.mp4\n",
                "[download] 50.0% of 10.0MiB at 1.0MiB/s ETA 00:05\n",
                "[download] 100% of 10.0MiB in 00:10\n",
                "__YTDLP_FINAL_PATH__:C:/Downloads/한글 제목.mp4\n",
            ]
        )

        result = wrapper._run_stdout_progress_loop(process, events.append, None)

        self.assertFalse(result.stopped)
        self.assertEqual(result.current_file, "sample.mp4")
        self.assertEqual(events[0]["status"], "downloading")
        self.assertEqual(events[0]["filename"], "sample.mp4")
        self.assertEqual(events[-1], {"status": "finished", "filename": "sample.mp4"})
        self.assertEqual(wrapper.final_output_path, "C:/Downloads/한글 제목.mp4")

    def test_stdout_progress_loop_returns_stopped_when_stop_check_requests_stop(self):
        wrapper = YtDlpWrapper("yt-dlp.exe")
        process = FakeProcess(["[download] Destination: sample.mp4\n"])
        killed = []

        def fake_kill(proc, graceful=False):
            killed.append((proc, graceful))

        wrapper._kill_process = fake_kill

        result = wrapper._run_stdout_progress_loop(process, lambda data: None, lambda: True)

        self.assertTrue(result.stopped)
        self.assertEqual(killed, [(process, False)])


if __name__ == "__main__":
    unittest.main()
