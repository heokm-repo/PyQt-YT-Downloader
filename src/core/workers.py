import queue
import threading
from typing import Any, Dict, Optional, Tuple

import yt_dlp
from PyQt5.QtCore import QThread, pyqtSignal

from core.download import handler as download_handler
from core.download.file_finder import find_downloaded_file
from core.worker_progress import apply_downloading_progress, apply_postprocessing_progress, format_speed
from core.worker_queue import parse_task_wrapper
from utils.logger import log
from utils.settings_store import get_download_folder
from constants import (
    MSG_PAUSED_BY_USER, QUEUE_TIMEOUT_SEC,
    STATUS_DOWNLOADING, STATUS_FINISHED, STATUS_POSTPROCESSING
)
from locales.strings import STR

class PlaylistAnalysisWorker(QThread):
    """플레이리스트 분석을 위한 별도 스레드 (UI 프리징 방지)"""
    analysis_finished = pyqtSignal(str, list, bool, str)
    
    def __init__(self, url: str, parent: Optional[QThread] = None):
        super().__init__(parent)
        self.url = url
    
    def run(self) -> None:
        """플레이리스트에서 비디오 ID 추출"""
        video_ids, success, error_msg = download_handler.extract_playlist_video_ids(self.url)
        self.analysis_finished.emit(self.url, video_ids, success, error_msg)


class DownloadWorker(QThread):
    """다운로드 작업을 처리하는 워커 스레드 (Queue 방식)"""
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
        self.current_output_path: str = ""
        self.retire_flag: bool = False

    # ============================================================
    # 헬퍼 메서드들
    # ============================================================
    
    def _extract_task_data(self, task_wrapper: Any) -> Optional[Tuple[int, str, Dict, Dict, bool, Optional[int]]]:
        """
        Parse a queue entry into (task_id, url, settings, metadata, is_resume, generation).
        Return None for shutdown markers or invalid queue entries.
        """
        task_data, should_mark_done = parse_task_wrapper(task_wrapper)
        if should_mark_done:
            self.download_queue.task_done()
        return task_data

    def _should_skip_task(self, task_id: int, generation: Optional[int] = None) -> bool:
        """Return True when the queued task should be skipped."""
        scheduler = self.parent()
        if scheduler and generation is not None and hasattr(scheduler, 'is_current_generation'):
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

    def _stop_check(self) -> bool:
        """정지/일시정지 여부를 빠르게 확인 (매 stdout 라인마다 호출됨)"""
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

    def _process_metadata(self, task_id: int, url: str, metadata: Dict, settings: Dict = None) -> Tuple[Dict, bool]:
        """
        메타데이터가 없으면 조회 (Lazy Loading).
        
        Returns:
            (메타데이터 딕셔너리, 성공 여부) 튜플
        """
        if not metadata or not metadata.get('title'):
            meta, meta_success = download_handler.fetch_metadata(url, settings)
            if meta_success and meta:
                metadata = meta
                self.metadata_fetched.emit(task_id, metadata)
            else:
                log.warning(f"메타데이터 조회 실패 (task_id={task_id}): {url}")
                return metadata, False
        return metadata, True

    def _init_progress_tracking(self, task_id: int, metadata: Dict) -> None:
        """진행률 추적 초기화 (비디오/오디오 구분)"""
        video_size_est = metadata.get('video_size', 0) or 0
        audio_size_est = metadata.get('audio_size', 0) or 0
        
        self.download_progress[task_id] = {
            'video': {'downloaded': 0, 'total': video_size_est, 'filename': None},
            'audio': {'downloaded': 0, 'total': audio_size_est, 'filename': None},
            'postprocessing': False,
            'total_size_est': video_size_est + audio_size_est,
            'video_size_est': video_size_est,
            'audio_size_est': audio_size_est
        }
        self.last_update_times[task_id] = 0.0

    def _find_downloaded_file(self, task_id: int, metadata: Dict, settings: Dict) -> str:
        """
        다운로드 완료된 파일의 경로를 찾아서 반환.
        찾지 못하면 빈 문자열 반환.
        """
        save_path = get_download_folder(settings)
        return find_downloaded_file(self.current_output_path, metadata, save_path, task_id)

    def _format_speed(self, speed: float) -> str:
        """바이트/초를 읽기 쉬운 형식으로 변환"""
        return format_speed(speed)

    # ============================================================
    # 메인 실행 메서드
    # ============================================================
        
    def run(self) -> None:
        """Queue에서 다운로드 작업을 순차적으로 처리"""
        while not self.stop_event.is_set():
            if self.retire_flag:
                break

            self.pause_event.wait()
            
            if self.stop_event.is_set():
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
                
                self.current_task_id = task_id
                self.current_generation = generation
                self.current_output_path = ""
                
                metadata, meta_ok = self._process_metadata(task_id, url, metadata, current_settings)
                
                # 메타데이터 조회 실패 시 다운로드 시도 없이 실패 처리
                if not meta_ok:
                    from utils.utils import is_youtube_url
                    if not is_youtube_url(url):
                        # 지원되지 않는 URL: 다운로드 시도 없이 즉시 실패
                        error_msg = STR.ERR_UNSUPPORTED_URL
                        log.error(f"지원되지 않는 URL (task_id={task_id}): {url}")
                        self.download_finished.emit(False, error_msg, task_id, "")
                        self.download_queue.task_done()
                        self.current_generation = None
                        continue
                
                self.task_started.emit(task_id)

                self._init_progress_tracking(task_id, metadata)

                success, message = download_handler.download_video(
                    url, current_settings, self._progress_hook, is_resume, self._stop_check
                )
                
                if not success and MSG_PAUSED_BY_USER in str(message):
                    self.download_finished.emit(False, STR.STATUS_PAUSED, task_id, "")
                    self.download_queue.task_done()
                    self.current_generation = None
                    continue

                if task_id in self.download_progress:
                    del self.download_progress[task_id]
                
                final_path = ""
                if success:
                    final_path = self._find_downloaded_file(task_id, metadata, current_settings)
                
                self.download_finished.emit(success, message, task_id, final_path)
                self.download_queue.task_done()
                self.current_generation = None
                
                if self.retire_flag:
                    break
                
            except queue.Empty:
                continue
            except Exception as e:
                self._handle_unexpected_error(e, task_wrapper)

    def _handle_unexpected_error(self, e: Exception, task_wrapper: Any) -> None:
        """예상치 못한 오류 처리"""
        error_task_id = -1
        if task_wrapper is not None:
            try:
                if isinstance(task_wrapper, tuple) and len(task_wrapper) == 7:
                    error_task_id = task_wrapper[2]
                elif isinstance(task_wrapper, tuple) and len(task_wrapper) > 1:
                    error_task_id = task_wrapper[1]
                self.download_queue.task_done()
            except (IndexError, TypeError, ValueError) as cleanup_error:
                log.debug(f"Failed to mark errored queue entry done: {cleanup_error}")
        error_msg = str(e)
        log.error(f"다운로드 오류 (task_id={error_task_id}): {error_msg}", exc_info=True)
        self.download_finished.emit(False, f"오류: {error_msg}", error_task_id, "")

    def _progress_hook(self, d: Dict[str, Any]) -> None:
        """진행률 훅 - concurrent_fragment_downloads 사용 시 정상 작동"""
        if self.stop_event.is_set():
            raise yt_dlp.utils.DownloadError(STR.WORKER_MSG_STOPPED)
        
        if not self.pause_event.is_set():
            raise yt_dlp.utils.DownloadError(MSG_PAUSED_BY_USER)
        
        task_id = self.current_task_id
        scheduler = self.parent()
        if scheduler and hasattr(scheduler, 'is_task_cancelled'):
            if scheduler.is_task_cancelled(task_id):
                raise yt_dlp.utils.DownloadError(MSG_PAUSED_BY_USER)
        if scheduler and hasattr(scheduler, 'is_task_paused'):
            if scheduler.is_task_paused(task_id):
                raise yt_dlp.utils.DownloadError(MSG_PAUSED_BY_USER)

        if d.get('filename'):
            self.current_output_path = d.get('filename')

        try:
            status = d.get('status', '')
            
            if status == STATUS_DOWNLOADING:
                self._handle_downloading_status(d, task_id)
            elif status in [STATUS_POSTPROCESSING, STATUS_FINISHED]:
                self._handle_postprocessing_status(d, status, task_id)
                
        except Exception as e:
            log.warning(f"Progress update handling failed (task_id={task_id}): {e}", exc_info=True)

    def _handle_downloading_status(self, d: Dict[str, Any], task_id: int) -> None:
        """다운로드 중 상태 처리"""
        if task_id not in self.download_progress:
            return

        apply_downloading_progress(d, self.download_progress[task_id])

        import time
        current_time = time.time()
        # 쓰레드 부하를 줄여 UI 프리징/렉을 방지하기 위해 0.1초 딜레이(100ms) 적용
        if current_time - self.last_update_times.get(task_id, 0.0) >= 0.1:
            self.progress_updated.emit(d, task_id)
            self.last_update_times[task_id] = current_time

    def _handle_postprocessing_status(self, d: Dict[str, Any], status: str, task_id: int) -> None:
        """후처리/완료 상태 처리"""
        if task_id not in self.download_progress:
            return

        if apply_postprocessing_progress(d, status, self.download_progress[task_id]):
            self.progress_updated.emit(d, task_id)


class StartupWorker(QThread):
    """앱 시작 시 메인 스레드를 차단하지 않고 무거운 검사(업데이트 확인 등)를 수행하는 워커"""
    status_updated = pyqtSignal(str)
    finished_checks = pyqtSignal(dict, tuple) # bin_updates, app_update_info (avail, latest, url)
    error_occurred = pyqtSignal(str)

    def run(self):
        try:
            from utils.bin.manager import check_binaries_exist, check_updates_available
            from utils.app_updater import check_for_updates
            from locales.strings import STR
            import time
            
            # 외부 구성 요소 확인
            self.status_updated.emit(STR.MSG_STARTUP_CHECK_EXT)
            time.sleep(0.1) # UI 업데이트 여유시간 (자율 조절)
            
            bin_updates = {}
            if check_binaries_exist():
                bin_updates = check_updates_available()
                
            # 앱 자체 업데이트 확인
            self.status_updated.emit(STR.MSG_STARTUP_CHECK_APP)
            app_update_info = check_for_updates()
            
            self.finished_checks.emit(bin_updates, app_update_info)
            
        except Exception as e:
            from utils.logger import log
            log.error(f"StartupWorker error: {e}", exc_info=True)
            self.error_occurred.emit(str(e))