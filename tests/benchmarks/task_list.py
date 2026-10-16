"""M2/M4: actual card registration, ordering, selection and removal costs."""

from __future__ import annotations

from collections import Counter
from contextlib import ExitStack
import time
from unittest.mock import patch

from .fixtures import expected_order, STATUSES
from .measurements import distribution, process_memory
from .ui_session import offline_window


def _observe(stack, owner, name, counts, key=None):
    original = getattr(owner, name)

    def counted(*args, **kwargs):
        counts[key or name] += 1
        return original(*args, **kwargs)

    stack.enter_context(patch.object(owner, name, counted))


def _heartbeat_operation(operation):
    """Sample 5ms event-loop lateness before, during and after registration."""
    from PyQt5.QtCore import QEventLoop, QTimer

    loop, timer = QEventLoop(), QTimer()
    timer.setInterval(5)
    previous = time.perf_counter()
    lateness, errors = [], []

    def tick():
        nonlocal previous
        now = time.perf_counter()
        lateness.append(max(0, (now - previous) * 1000 - 5))
        previous = now

    def execute():
        try:
            operation()
        except Exception as exc:
            errors.append(exc)
        finally:
            QTimer.singleShot(50, loop.quit)

    timer.timeout.connect(tick)
    timer.start()
    QTimer.singleShot(50, execute)
    loop.exec_()
    timer.stop()
    if errors:
        raise errors[0]
    return lateness


def list_sample(app, settings: dict, count: int) -> dict:
    from PyQt5.QtCore import Qt
    from PyQt5.QtNetwork import QNetworkAccessManager
    from constants import TaskStatus
    from gui.windows import main_window
    from gui.tasks import task_status_message
    from gui.tasks import task_list_controller

    before = process_memory()
    with offline_window(app, settings) as window, ExitStack() as stack:
        counts = Counter()
        for name in ("_sorted_task_ids",):
            _observe(stack, window, name, counts)
        for name in ("removeWidget", "insertWidget"):
            _observe(stack, window.task_layout, name, counts)
        _observe(stack, main_window, "summarize_task_progress", counts, "summary")
        _observe(stack, task_status_message, "summarize_task_progress", counts, "summary")
        _observe(stack, task_list_controller, "summarize_task_progress", counts, "summary")
        _observe(stack, window.scheduler, "add_task", counts, "enqueue")
        registration = {}

        def register():
            start = time.perf_counter()
            window._register_playlist_tasks([f"v{i:010d}" for i in range(count)])
            registration.update(elapsed_ms=(time.perf_counter() - start) * 1000,
                                calls=dict(counts))

        lateness = _heartbeat_operation(register)
        assert [task.id for task in window.tasks] == list(range(1, count + 1))
        assert counts["enqueue"] == count
        records = []
        for i, task in enumerate(window.tasks):
            task.status = TaskStatus.from_string(STATUSES[i % len(STATUSES)])
            records.append({"id": task.id, "status": task.status.value})
        sorts = {}
        for mode in ("newest", "oldest", "status"):
            window.task_sort_button.setCurrentKey(mode)
            counts.clear()
            start = time.perf_counter()
            window._apply_task_sort_order()
            elapsed_ms = (time.perf_counter() - start) * 1000
            order = expected_order(records, mode)
            assert window.visible_task_order == order
            assert [window.task_layout.itemAt(i).widget().task_id for i in range(count)] == order
            assert [task.id for task in window.tasks] == list(range(1, count + 1))
            selection = window.selection_manager
            selection.handle_click(order[0], Qt.NoModifier, window.task_widgets, window.task_layout)
            selection.handle_click(order[2], Qt.ShiftModifier, window.task_widgets, window.task_layout)
            assert set(selection.get_selected_ids()) == set(order[:3])
            selection.handle_click(order[1], Qt.ControlModifier, window.task_widgets, window.task_layout)
            assert set(selection.get_selected_ids()) == {order[0], order[2]}
            sorts[mode] = {"elapsed_ms": elapsed_ms, "calls": dict(counts), "order": order}
        counts.clear()
        window._apply_task_sort_order()
        unchanged = dict(counts)
        populated_memory = process_memory()
        managers = len(window.findChildren(QNetworkAccessManager))
        counts.clear()
        start = time.perf_counter()
        with patch.object(window.task_actions, "_confirm_question", return_value=True):
            assert window.task_actions.remove_selected_from_list(list(range(1, count + 1)))
        removal = {"elapsed_ms": (time.perf_counter() - start) * 1000, "calls": dict(counts)}
        assert not window.tasks and not window.task_widgets
        assert not window.visible_task_order
    return {"registration": registration, "sorts": sorts, "unchanged_order_calls": unchanged,
            "removal": removal, "network_managers": managers, "heartbeat_lateness_ms": lateness,
            "memory_before": before, "memory_populated": populated_memory,
            "memory_after_deletion": process_memory()}


def benchmark_lists(app, settings: dict, sizes: list[int], repeats: int) -> list[dict]:
    results = []
    for count in sizes:
        list_sample(app, settings, count)  # warm-up is excluded
        samples = []
        for iteration in range(repeats):
            samples.append(list_sample(app, settings, count))
            print(f"M2 tasks={count} sample={iteration + 1}/{repeats}", flush=True)
        results.append({
            "tasks": count, "warmups": 1, "samples": samples,
            "registration_ms": distribution([s["registration"]["elapsed_ms"] for s in samples]),
            "removal_ms": distribution([s["removal"]["elapsed_ms"] for s in samples]),
            "heartbeat_lateness_ms": distribution([v for s in samples for v in s["heartbeat_lateness_ms"]]),
        })
    return results
