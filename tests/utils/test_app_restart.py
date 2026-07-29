import os
import sys
import unittest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
SRC = os.path.join(ROOT, "src")
if SRC not in sys.path:
    sys.path.insert(0, SRC)

from utils.app_restart import (
    RESTART_WAIT_PID_ARG,
    RestartCommand,
    build_restart_command,
    launch_restart,
    split_restart_wait_argument,
    wait_for_restart_parent,
)


class AppRestartTests(unittest.TestCase):
    def test_source_restart_uses_python_and_absolute_script_path(self):
        command = build_restart_command(
            executable="python.exe",
            argv=["src/main.py", "--example"],
            working_directory=ROOT,
            is_frozen=False,
            parent_pid=123,
        )

        self.assertEqual(command.program, "python.exe")
        self.assertEqual(
            command.arguments,
            (
                os.path.abspath("src/main.py"),
                "--example",
                RESTART_WAIT_PID_ARG,
                "123",
            ),
        )
        self.assertEqual(command.working_directory, ROOT)

    def test_packaged_restart_does_not_repeat_executable_argument(self):
        command = build_restart_command(
            executable="YTDownloader.exe",
            argv=["YTDownloader.exe", "--example"],
            working_directory=ROOT,
            is_frozen=True,
            parent_pid=123,
        )

        self.assertEqual(
            command.arguments,
            ("--example", RESTART_WAIT_PID_ARG, "123"),
        )

    def test_restart_command_replaces_previous_internal_wait_argument(self):
        command = build_restart_command(
            executable="YTDownloader.exe",
            argv=["YTDownloader.exe", RESTART_WAIT_PID_ARG, "11"],
            working_directory=ROOT,
            is_frozen=True,
            parent_pid=22,
        )

        self.assertEqual(command.arguments, (RESTART_WAIT_PID_ARG, "22"))

    def test_launch_restart_normalizes_qprocess_tuple(self):
        calls = []
        command = RestartCommand("app.exe", ("--flag",), ROOT)

        launched = launch_restart(
            command,
            lambda program, arguments, cwd: (
                calls.append((program, arguments, cwd)) or True,
                1234,
            ),
        )

        self.assertTrue(launched)
        self.assertEqual(calls, [("app.exe", ["--flag"], ROOT)])

    def test_launch_restart_reports_failure(self):
        command = RestartCommand("app.exe", (), ROOT)

        self.assertFalse(
            launch_restart(command, lambda program, arguments, cwd: (False, 0))
        )

    def test_split_restart_wait_argument_preserves_unrelated_arguments(self):
        cleaned, process_id = split_restart_wait_argument(
            ["app.exe", "--flag", RESTART_WAIT_PID_ARG, "123"]
        )

        self.assertEqual(cleaned, ["app.exe", "--flag"])
        self.assertEqual(process_id, 123)

    def test_wait_for_restart_parent_consumes_argument_and_uses_waiter(self):
        argv = ["app.exe", RESTART_WAIT_PID_ARG, "123", "--flag"]
        calls = []

        waited = wait_for_restart_parent(
            argv,
            timeout_ms=456,
            waiter=lambda process_id, timeout: (
                calls.append((process_id, timeout)) or True
            ),
        )

        self.assertTrue(waited)
        self.assertEqual(argv, ["app.exe", "--flag"])
        self.assertEqual(calls, [(123, 456)])


if __name__ == "__main__":
    unittest.main()
