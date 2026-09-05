import queue
import threading
from typing import Any, Dict, Optional, Tuple

from PyQt5.QtCore import QThread, pyqtSignal

from core.download import handler as download_handler
from core.download.workspace_identity import (
    LEGACY_WORKSPACE_SETTING,
    WORKSPACE_ID_SETTING,
)
from core.worker_progress import apply_downloading_progress, apply_postprocessing_progress
from core.worker_queue import parse_task_wrapper
from utils.logger import log
from constants import (
    MSG_PAUSED_BY_USER, QUEUE_TIMEOUT_SEC, STARTUP_STATUS_SETTLE_DELAY_SEC,
    STATUS_DOWNLOADING, STATUS_FINISHED, STATUS_POSTPROCESSING
)
from locales.strings import STR


class DownloadInterruptedError(RuntimeError):
    """Signal that the app requested the external download process to stop."""


class PlaylistAnalysisWorker(QThread):
    """Worker thread for playlist analysis without freezing the UI."""
    analysis_finished = pyqtSignal(str, list, bool, str, int)
    
    def __init__(self, url: str, parent: Optional[QThread] = None):
        super().__init__(parent)
        self.url = url
    
    def run(self) -> None:
        """Extract video IDs from a playlist."""
        video_ids, success, error_msg, entry_count = download_handler.extract_playlist_video_ids(self.url)
        self.analysis_finished.emit(self.url, video_ids, success, error_msg, entry_count)


class DownloadWorker(QThread):
    """Queue-based worker thread that handles download tasks."""
    progress_updated = pyqtSignal(dict, int)
    download_finished = pyqtSignal(bool, str, int, str)
    task_started = pyqtSignal(int)
    metadata_fetched = pyqtSignal(int, dict)
    
    def __init__(
        self, 
        download_queue: queue.PriorityQueue, 
        stop_event: threading.Event, 
        pause_event: threading.Event, 
        parent: Optional[QThread] = None
    ):
        super().__init__(parent)
        self.download_queue = download_queue
        self.stop_event = stop_event
        self.pause_event = pause_event
        self.current_task_id: int = -1
        self.current_generation: Optional[int] = None
        self.download_progress: Dict[int, Dict[str, Any]] = {}
        self.last_update_times: Dict[int, float] = {}
        self.retire_flag: bool = False

    # ============================================================
    # Helper methods.
    # ============================================================
    
    def _extract_task_data(self, task_wrapper: Any) -> Optional[Tuple[int, str, Dict, Dict, bool, int]]:
        """
        Parse a queue entry into (task_id, url, settings, metadata, is_resume, generation).
        Return None for the scheduler shutdown marker.
        """
        task_data, should_mark_done = parse_task_wrapper(task_wrapper)
        if should_mark_done:
            self.download_queue.task_done()
        return task_data

    def _should_skip_task(self, task_id: int, generation: int) -> bool:
        """Return True when the queued task should be skipped."""
        scheduler = self.parent()
        if scheduler and hasattr(scheduler, 'is_current_generation'):
            if not scheduler.is_current_generation(task_id, generation):
                log.info(f"Skipping stale queued task (task_id={task_id}, generation={generation})")
                self.download_queue.task_done()
                return True

        if scheduler and hasattr(scheduler, 'is_task_cancelled'):
            if scheduler.is_task_cancelled(task_id):
                self.download_queue.task_done()
                return True

        if scheduler and hasattr(scheduler, 'is_task_paused'):
            if scheduler.is_task_paused(task_id):
                self.download_queue.task_done()
                return True
        return False

    def _claim_task(self, task_id: int, generation: int) -> bool:
        """Atomically claim a task after the fast skip checks."""
        scheduler = self.parent()
        if scheduler and hasattr(scheduler, "claim_task"):
            return scheduler.claim_task(task_id, generation)
        return True

    def _release_current_claim(self) -> None:
        """Release scheduler ownership of the current task generation."""
        task_id = self.current_task_id
        generation = self.current_generation
        scheduler = self.parent()
        if (
            scheduler
            and generation is not None
            and hasattr(scheduler, "release_task")
        ):
            scheduler.release_task(task_id, generation)
        self.current_task_id = -1
        self.current_generation = None

    def _finish_current_queue_entry(self) -> None:
        """Mark a claimed queue entry done and release worker ownership."""
        try:
            self.download_queue.task_done()
        finally:
            self._release_current_claim()

    def _stop_check(self) -> bool:
        """Quickly check stop and pause state for each stdout line."""
        if self.stop_event.is_set():
            return True
        if not self.pause_event.is_set():
            return True
        scheduler = self.parent()
        if scheduler and self.current_generation is not None and hasattr(scheduler, 'is_current_generation'):
            if not scheduler.is_current_generation(self.current_task_id, self.current_generation):
                return True
        if scheduler and hasattr(scheduler, 'is_task_cancelled'):
            if scheduler.is_task_cancelled(self.current_task_id):
                return True
        if scheduler and hasattr(scheduler, 'is_task_paused'):
            if scheduler.is_task_paused(self.current_task_id):
                return True
        return False

    def _init_progress_tracking(self, task_id: int, metadata: Dict) -> None:
        """Initialize progress tracking from the streams yt-dlp selected."""
        video_size_est = metadata.get('video_size', 0) or 0
        audio_size_est = metadata.get('audio_size', 0) or 0
        selected_streams = metadata.get("download_streams")
        streams = []
        if isinstance(selected_streams, list):
            for index, stream in enumerate(selected_streams):
                if not isinstance(stream, dict):
                    continue
                streams.append(
                    {
                        "id": str(stream.get("id") or index),
                        "kind": str(stream.get("kind") or "unknown"),
                        "downloaded": 0,
                        "total": stream.get("size", 0) or 0,
                        "filename": None,
                    }
                )
        
        progress_info = {
            'active_stream_index': 0,
            'video': {'downloaded': 0, 'total': video_size_est, 'filename': None},
            'audio': {'downloaded': 0, 'total': audio_size_est, 'filename': None},
            'postprocessing': False,
            'active_stream': 'video',
            'total_size_est': video_size_est + audio_size_est,
            'video_size_est': video_size_est,
            'audio_size_est': audio_size_est
        }
        if streams:
            progress_info['streams'] = streams
        self.download_progress[task_id] = progress_info
        self.last_update_times[task_id] = 0.0

    # ============================================================
    # Main execution method.
    # ============================================================
        
    def run(self) -> None:
        """Process download tasks from the queue sequentially."""
        while not self.stop_event.is_set():
            if self.retire_flag:
                break

            if not self.pause_event.wait(timeout=QUEUE_TIMEOUT_SEC):
                continue
            
            if self.stop_event.is_set() or self.retire_flag:
                break

            task_wrapper = None
            try:
                task_wrapper = self.download_queue.get(timeout=QUEUE_TIMEOUT_SEC)
                
                task_data = self._extract_task_data(task_wrapper)
                if task_data is None:
                    break
                
                task_id, url, current_settings, metadata, is_resume, generation = task_data

                if self._should_skip_task(task_id, generation):
                    continue
                if not self._claim_task(task_id, generation):
                    log.info(
                        "Skipping unclaimable queued task "
                        "(task_id=%s, generation=%s)",
                        task_id,
                        generation,
                    )
                    self.download_queue.task_done()
                    continue
                
                self.current_task_id = task_id
                self.current_generation = generation

                self._init_progress_tracking(task_id, metadata)

                task_started = False
                metadata_received = False

                def mark_task_started() -> None:
                    nonlocal task_started
                    if not task_started:
                        self.task_started.emit(task_id)
                        task_started = True

                def handle_metadata(fetched_metadata: Dict) -> None:
                    nonlocal metadata, metadata_received
                    if metadata_received or not fetched_metadata:
                        return
                    metadata_received = True
                    metadata = {**metadata, **fetched_metadata}
                    selected_audio_bitrate = fetched_metadata.get("audio_bitrate")
                    if selected_audio_bitrate:
                        execution_settings["_selected_audio_bitrate"] = (
                            selected_audio_bitrate
                        )
                    self._init_progress_tracking(task_id, metadata)
                    self.metadata_fetched.emit(task_id, metadata)
                    mark_task_started()

                def handle_progress(progress: Dict[str, Any]) -> None:
                    # Normally before_dl metadata arrives first. Keep progress
                    # functional if yt-dlp omits or cannot parse that output.
                    mark_task_started()
                    self._progress_hook(progress)

                execution_settings = dict(current_settings)
                legacy_identity = execution_settings.get(
                    LEGACY_WORKSPACE_SETTING
                )
                execution_settings["_temp_identity"] = {
                    "id": metadata.get("id"),
                    "extractor": metadata.get("extractor", "unknown"),
                    "workspace_id": execution_settings.get(
                        WORKSPACE_ID_SETTING
                    ),
                    "legacy_workspace": isinstance(legacy_identity, dict),
                    "legacy_identity": legacy_identity,
                }
                result = download_handler.download_video_with_result(
                    url,
                    execution_settings,
                    handle_progress,
                    is_resume=is_resume,
                    stop_check=self._stop_check,
                    metadata_hook=handle_metadata,
                )
                success = result.success
                message = result.message
                final_path = result.final_path
                
                if not success and MSG_PAUSED_BY_USER in str(message):
                    self.download_finished.emit(
                        False,
                        STR.STATUS_PAUSED,
                        task_id,
                        final_path,
                    )
                    self._finish_current_queue_entry()
                    continue

                if task_id in self.download_progress:
                    del self.download_progress[task_id]
                
                self.download_finished.emit(success, message, task_id, final_path)
                self._finish_current_queue_entry()
                
                if self.retire_flag:
                    break
                
            except queue.Empty:
                continue
            except Exception as e:
                self._handle_unexpected_error(e, task_wrapper)

    def _handle_unexpected_error(self, e: Exception, task_wrapper: Any) -> None:
        """Handle unexpected errors."""
        error_task_id = -1
        if task_wrapper is not None:
            try:
                if isinstance(task_wrapper, tuple) and len(task_wrapper) == 7:
                    error_task_id = task_wrapper[2]
                if (
                    self.current_generation is not None
                    and error_task_id == self.current_task_id
                ):
                    self._release_current_claim()
                self.download_queue.task_done()
            except (IndexError, TypeError, ValueError) as cleanup_error:
                log.debug(f"Failed to mark errored queue entry done: {cleanup_error}")
        error_msg = str(e)
        log.error(f"다운로드 오류 (task_id={error_task_id}): {error_msg}", exc_info=True)
        self.download_finished.emit(False, f"오류: {error_msg}", error_task_id, "")

    def _progress_hook(self, d: Dict[str, Any]) -> None:
        """Progress hook that works with concurrent_fragment_downloads."""
        if self.stop_event.is_set():
            raise DownloadInterruptedError(STR.WORKER_MSG_STOPPED)
        
        if not self.pause_event.is_set():
            raise DownloadInterruptedError(MSG_PAUSED_BY_USER)
        
        task_id = self.current_task_id
        scheduler = self.parent()
        if scheduler and hasattr(scheduler, 'is_task_cancelled'):
            if scheduler.is_task_cancelled(task_id):
                raise DownloadInterruptedError(MSG_PAUSED_BY_USER)
        if scheduler and hasattr(scheduler, 'is_task_paused'):
            if scheduler.is_task_paused(task_id):
                raise DownloadInterruptedError(MSG_PAUSED_BY_USER)

        try:
            status = d.get('status', '')
            
            if status == STATUS_DOWNLOADING:
                self._handle_downloading_status(d, task_id)
            elif status in [STATUS_POSTPROCESSING, STATUS_FINISHED]:
                self._handle_postprocessing_status(d, status, task_id)
                
        except Exception as e:
            log.warning(f"Progress update handling failed (task_id={task_id}): {e}", exc_info=True)

    def _handle_downloading_status(self, d: Dict[str, Any], task_id: int) -> None:
        """Handle the downloading status."""
        if task_id not in self.download_progress:
            return

        apply_downloading_progress(d, self.download_progress[task_id])

        import time
        current_time = time.time()
        # Throttle updates by 100 ms to reduce thread load and avoid UI stutter.
        if current_time - self.last_update_times.get(task_id, 0.0) >= 0.1:
            self.progress_updated.emit(d, task_id)
            self.last_update_times[task_id] = current_time

    def _handle_postprocessing_status(self, d: Dict[str, Any], status: str, task_id: int) -> None:
        """Handle postprocessing and finished statuses."""
        if task_id not in self.download_progress:
            return

        if apply_postprocessing_progress(d, status, self.download_progress[task_id]):
            self.progress_updated.emit(d, task_id)


class StartupWorker(QThread):
    """Worker that runs heavy startup checks without blocking the main thread."""
    status_updated = pyqtSignal(str)
    # bin_updates, app_update_info (available, latest, URL, SHA-256 digest)
    finished_checks = pyqtSignal(dict, tuple)
    error_occurred = pyqtSignal(str)

    def run(self):
        try:
            from utils.bin.manager import (
                check_binaries_exist,
                check_updates_available_strict,
            )
            from utils.app_updater import check_for_updates_strict
            from locales.strings import STR
            import time
            
            # Check external components.
            self.status_updated.emit(STR.MSG_STARTUP_CHECK_EXT)
            time.sleep(STARTUP_STATUS_SETTLE_DELAY_SEC) # Allow time for the UI status update.
            
            bin_updates = {}
            if check_binaries_exist():
                bin_updates = check_updates_available_strict()
                
            # Check for app self-updates.
            self.status_updated.emit(STR.MSG_STARTUP_CHECK_APP)
            app_update_info = check_for_updates_strict()
            
            self.finished_checks.emit(bin_updates, app_update_info)
            
        except Exception as e:
            from utils.logger import log
            log.error(f"StartupWorker error: {e}", exc_info=True)
            self.error_occurred.emit(str(e))
