"""Download scheduler that manages the worker thread pool and download queue."""
import threading
import queue

from PyQt5.QtCore import QObject, pyqtSignal

from core.workers import DownloadWorker
from utils.logger import log
from constants import WORKER_CLEANUP_WAIT_MS, SCHEDULER_PRIORITY_NORMAL


class DownloadScheduler(QObject):
    """Scheduler that manages download workers and the priority queue."""

    # Signals relayed to the main window.
    progress_updated = pyqtSignal(dict, int)  # progress data, task_id
    download_finished = pyqtSignal(bool, str, int, str)  # success flag, message, task_id, file path
    task_started = pyqtSignal(int)  # task_id
    metadata_fetched = pyqtSignal(int, dict)  # task_id, metadata

    def __init__(self, parent=None):
        super().__init__(parent)

        # Download priority queue.
        self.download_queue = queue.PriorityQueue()

        # Thread-control events.
        self.stop_event = threading.Event()
        self.pause_event = threading.Event()
        self.pause_event.set()  # Default state is running.

        # Worker list.
        self.workers = []

        # Per-task pause flags protected by a lock.
        self.task_paused_flags = {}
        self.task_cancelled_flags = set()
        self._paused_flags_lock = threading.Lock()

        # Keep only the latest queued run valid for each task_id.
        self.task_generations = {}
        self._active_task_generations = {}
        self._pending_task_entries = {}
        self._generations_lock = threading.Lock()

    def initialize(self, max_workers: int):
        """Initialize the scheduler and start workers."""
        self.stop_event.clear()
        self.adjust_worker_count(max_workers)

    def add_task(self, priority: int, task_id: int, url: str, settings: dict, metadata: dict = None, is_resume: bool = False):
        """Add a download task to the queue."""
        if metadata is None:
            metadata = {}
        with self._paused_flags_lock:
            self.task_cancelled_flags.discard(task_id)
        with self._generations_lock:
            generation = self.task_generations.get(task_id, 0) + 1
            self.task_generations[task_id] = generation
            entry = (priority, generation, task_id, url, settings, metadata, is_resume)
            if task_id in self._active_task_generations:
                self._pending_task_entries[task_id] = entry
            else:
                self.download_queue.put(entry)
        return generation

    def is_current_generation(self, task_id: int, generation: int) -> bool:
        """Return whether a queued task generation is still current."""
        with self._generations_lock:
            return self.task_generations.get(task_id) == generation

    def claim_task(self, task_id: int, generation: int) -> bool:
        """Atomically claim a still-current task generation for one worker."""
        with self._paused_flags_lock:
            if (
                task_id in self.task_cancelled_flags
                or self.task_paused_flags.get(task_id, False)
            ):
                return False
            with self._generations_lock:
                if self.task_generations.get(task_id) != generation:
                    return False
                if task_id in self._active_task_generations:
                    return False
                self._active_task_generations[task_id] = generation
                return True

    def release_task(self, task_id: int, generation: int) -> None:
        """Release a worker claim without affecting a newer generation."""
        with self._generations_lock:
            if self._active_task_generations.get(task_id) == generation:
                del self._active_task_generations[task_id]
                entry = self._pending_task_entries.pop(task_id, None)
                if entry and not self.stop_event.is_set():
                    self.download_queue.put(entry)

    def is_task_running(self, task_id: int) -> bool:
        """Return whether a worker still owns a generation for this task."""
        with self._generations_lock:
            return task_id in self._active_task_generations

    def pause_all(self):
        """Pause all downloads."""
        self.pause_event.clear()

    def resume_all(self):
        """Resume all downloads."""
        self.pause_event.set()

    def pause_task(self, task_id: int):
        """Set the pause flag for one task in a thread-safe way."""
        with self._paused_flags_lock:
            self.task_paused_flags[task_id] = True

    def resume_task(self, task_id: int):
        """Clear the pause flag for one task in a thread-safe way."""
        with self._paused_flags_lock:
            if task_id in self.task_paused_flags:
                del self.task_paused_flags[task_id]

    def cancel_task(self, task_id: int):
        """Cancel queued or currently running work for a task."""
        with self._paused_flags_lock:
            self.task_paused_flags.pop(task_id, None)
            self.task_cancelled_flags.add(task_id)
        with self._generations_lock:
            self.task_generations[task_id] = self.task_generations.get(task_id, 0) + 1
            self._pending_task_entries.pop(task_id, None)

    def is_task_cancelled(self, task_id: int) -> bool:
        """Return whether a task was cancelled by the UI."""
        with self._paused_flags_lock:
            return task_id in self.task_cancelled_flags

    def is_task_paused(self, task_id: int) -> bool:
        """Return whether one task is paused in a thread-safe way."""
        with self._paused_flags_lock:
            return self.task_paused_flags.get(task_id, False)

    def adjust_worker_count(self, target_count: int):
        """
        Adjust the worker count dynamically.

        When scaling up, create additional workers. When scaling down, ask excess workers to retire after their current task.
        """
        # Remove workers that already stopped.
        self.workers = [w for w in self.workers if w.isRunning()]

        available_workers = [w for w in self.workers if not w.retire_flag]
        current_count = len(available_workers)

        if target_count > current_count:
            # Add missing workers when scaling up.
            needed = target_count - current_count
            log.info(f"워커 {needed}명 증원 (현재 {current_count} -> 목표 {target_count})")

            for _ in range(needed):
                worker = DownloadWorker(
                    self.download_queue,
                    self.stop_event,
                    self.pause_event,
                    self  # Pass the scheduler as the parent.
                )
                # Relay worker signals through scheduler signals.
                worker.progress_updated.connect(self.progress_updated)
                worker.download_finished.connect(self._on_download_finished)
                worker.task_started.connect(self.task_started)
                worker.metadata_fetched.connect(self.metadata_fetched)
                worker.start()
                self.workers.append(worker)

        elif target_count < current_count:
            # Ask extra workers to retire after their current task.
            to_retire = current_count - target_count
            log.info(f"워커 {to_retire}명 감원 예약 (현재 {current_count} -> 목표 {target_count})")

            for worker in available_workers[-to_retire:]:
                worker.retire_flag = True

    def _on_download_finished(self, success: bool, message: str, task_id: int, final_path: str):
        """Relay a completed download signal after removing dead workers."""
        # Remove dead threads.
        self.workers = [w for w in self.workers if w.isRunning()]
        # Relay the signal.
        self.download_finished.emit(success, message, task_id, final_path)

    def shutdown(self):
        """Shut down the scheduler and clean up all workers."""
        # Send the global shutdown signal.
        self.stop_event.set()
        self.pause_event.set()

        # Send shutdown markers through the queue.
        for _ in self.workers:
            self.download_queue.put((SCHEDULER_PRIORITY_NORMAL, -1, None))

        # Give workers time to clean up.
        for worker in self.workers:
            if worker.isRunning():
                worker.wait(WORKER_CLEANUP_WAIT_MS)

        self.workers = [worker for worker in self.workers if worker.isRunning()]
        return not self.workers
