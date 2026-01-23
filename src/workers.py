import queue
import os
import threading
import unicodedata
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import yt_dlp
from PyQt5.QtCore import QThread, pyqtSignal

import youtube_handler
from logger import log
from constants import (
    MSG_PAUSED_BY_USER, MEDIA_EXTENSIONS, QUEUE_TIMEOUT_SEC,
    BYTES_PER_KB, BYTES_PER_MB
)

class PlaylistAnalysisWorker(QThread):
    """플레이리스트 분석을 위한 별도 스레드 (UI 프리징 방지)"""
    analysis_finished = pyqtSignal(str, list, bool, str)
    
    def __init__(self, url: str, parent: Optional[QThread] = None):
        super().__init__(parent)
        self.url = url
    
    def run(self) -> None:
        """플레이리스트에서 비디오 ID 추출"""
        video_ids, success, error_msg = youtube_handler.extract_playlist_video_ids(self.url)
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
        self.download_progress: Dict[int, Dict[str, Any]] = {}
        self.current_output_path: str = ""
        self.retire_flag: bool = False

    # ============================================================
    # 헬퍼 메서드들
    # ============================================================
    
    def _extract_task_data(self, task_wrapper: Any) -> Optional[Tuple[int, str, Dict, Dict]]:
        """
        Queue에서 가져온 데이터를 파싱하여 (task_id, url, settings, metadata) 튜플 반환.
        종료 신호이거나 파싱 실패 시 None 반환.
        """
        if task_wrapper is None:
            return None
            
        if isinstance(task_wrapper, tuple):
            task = task_wrapper[1:]
            if task[0] is None:
                self.download_queue.task_done()
                return None
        else:
            task = task_wrapper

        if len(task) == 4:
            task_id, url, task_settings, metadata = task
        else:
            task_id, url, task_settings = task
            metadata = {}
        
        return task_id, url, task_settings, metadata

    def _should_skip_task(self, task_id: int) -> bool:
        """개별 작업 일시정지 여부 확인. 스킵해야 하면 True 반환."""
        scheduler = self.parent()
        if scheduler and hasattr(scheduler, 'is_task_paused'):
            if scheduler.is_task_paused(task_id):
                self.download_queue.task_done()
                return True
        return False

    def _process_metadata(self, task_id: int, url: str, metadata: Dict, settings: Dict = None) -> Dict:
        """
        메타데이터가 없으면 조회 (Lazy Loading).
        조회된 메타데이터 반환.
        """
        if not metadata or not metadata.get('title'):
            meta, meta_success = youtube_handler.fetch_metadata(url, settings)
            if meta_success and meta:
                metadata = meta
                self.metadata_fetched.emit(task_id, metadata)
            else:
                log.warning(f"메타데이터 조회 실패 (task_id={task_id}): {url}")
        return metadata

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

    def _find_downloaded_file(self, task_id: int, metadata: Dict, settings: Dict) -> str:
        """
        다운로드 완료된 파일의 경로를 찾아서 반환.
        찾지 못하면 빈 문자열 반환.
        """
        final_path = ""
        
        if self.current_output_path:
            try:
                captured_path = Path(self.current_output_path).resolve()
                if captured_path.exists():
                    return str(captured_path)
            except Exception:
                pass
        
        save_path = settings.get('download_folder') or settings.get('save_path') or os.getcwd()
        save_dir = Path(save_path)
        
        if not save_dir.exists():
            return final_path
            
        try:
            video_title = metadata.get('title', '')
            if video_title:
                safe_title = unicodedata.normalize('NFC', video_title)
                fullwidth_map = str.maketrans({
                    '<': '＜', '>': '＞', ':': '：', '"': '＂',
                    '/': '／', '\\': '＼', '|': '｜', '?': '？', '*': '＊'
                })
                safe_title = safe_title.translate(fullwidth_map)
                
                for file_path in save_dir.iterdir():
                    if not file_path.is_file():
                        continue
                    
                    f_stem = unicodedata.normalize('NFC', file_path.stem)
                    
                    if safe_title.lower() in f_stem.lower():
                        if file_path.suffix.lower() in MEDIA_EXTENSIONS:
                            final_path = str(file_path.resolve())
                            break
                            
        except Exception as e:
            log.warning(f"파일 경로 찾기 실패 (task_id={task_id}): {e}")
        
        return final_path

    def _format_speed(self, speed: float) -> str:
        """바이트/초를 읽기 쉬운 형식으로 변환"""
        if speed > BYTES_PER_MB:
            return f"{speed / BYTES_PER_MB:.1f} MB/s"
        else:
            return f"{speed / BYTES_PER_KB:.1f} KB/s"

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
                
                task_id, url, current_settings, metadata = task_data

                if self._should_skip_task(task_id):
                    continue
                
                self.current_task_id = task_id
                self.current_output_path = ""
                
                metadata = self._process_metadata(task_id, url, metadata, current_settings)
                
                self.task_started.emit(task_id)

                self._init_progress_tracking(task_id, metadata)

                success, message = youtube_handler.download_video(
                    url, current_settings, self._progress_hook
                )
                
                if not success and MSG_PAUSED_BY_USER in str(message):
                    self.download_finished.emit(False, "일시정지됨", task_id, "")
                    self.download_queue.task_done()
                    continue

                if task_id in self.download_progress:
                    del self.download_progress[task_id]
                
                final_path = ""
                if success:
                    final_path = self._find_downloaded_file(task_id, metadata, current_settings)
                
                self.download_finished.emit(success, message, task_id, final_path)
                self.download_queue.task_done()
                
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
                if isinstance(task_wrapper, tuple) and len(task_wrapper) > 1:
                    error_task_id = task_wrapper[1]
                self.download_queue.task_done()
            except Exception:
                pass
        error_msg = str(e)
        log.error(f"다운로드 오류 (task_id={error_task_id}): {error_msg}", exc_info=True)
        self.download_finished.emit(False, f"오류: {error_msg}", error_task_id, "")

    def _progress_hook(self, d: Dict[str, Any]) -> None:
        """진행률 훅 - concurrent_fragment_downloads 사용 시 정상 작동"""
        if self.stop_event.is_set():
            raise yt_dlp.utils.DownloadError("사용자에 의해 다운로드 중단됨")
        
        if not self.pause_event.is_set():
            raise yt_dlp.utils.DownloadError(MSG_PAUSED_BY_USER)
        
        task_id = self.current_task_id
        scheduler = self.parent()
        if scheduler and hasattr(scheduler, 'is_task_paused'):
            if scheduler.is_task_paused(task_id):
                raise yt_dlp.utils.DownloadError(MSG_PAUSED_BY_USER)

        if d.get('filename'):
            self.current_output_path = d.get('filename')

        try:
            status = d.get('status', '')
            
            if status == 'downloading':
                self._handle_downloading_status(d, task_id)
            elif status in ['postprocessing', 'finished']:
                self._handle_postprocessing_status(d, status, task_id)
                
        except Exception:
            pass

    def _handle_downloading_status(self, d: Dict[str, Any], task_id: int) -> None:
        """다운로드 중 상태 처리"""
        current_real_total = d.get('total_bytes') or d.get('total_bytes_estimate', 0)
        downloaded = d.get('downloaded_bytes', 0) or 0
        current_filename = d.get('filename', '')
        
        if task_id not in self.download_progress:
            return

        progress_info = self.download_progress[task_id]
        
        import os
        clean_current = os.path.basename(current_filename)
        for ext in ['.part', '.ytdl']:
            if clean_current.endswith(ext):
                clean_current = clean_current[:-len(ext)]
                break
            
        saved_video_name = progress_info['video'].get('filename')
        if saved_video_name: 
            saved_video_name = os.path.basename(saved_video_name)
            
        saved_audio_name = progress_info['audio'].get('filename')
        if saved_audio_name: 
            saved_audio_name = os.path.basename(saved_audio_name)

        is_video_file = False
        is_audio_file = False
        
        if saved_video_name and clean_current == saved_video_name:
            is_video_file = True
        elif saved_audio_name and clean_current == saved_audio_name:
            is_audio_file = True
        else:
            if saved_video_name is None and saved_audio_name is None:
                progress_info['video']['filename'] = clean_current
                is_video_file = True
            elif saved_video_name is None:
                progress_info['video']['filename'] = clean_current
                is_video_file = True
            elif saved_audio_name is None:
                progress_info['audio']['filename'] = clean_current
                is_audio_file = True

        if is_video_file:
            progress_info['video']['downloaded'] = downloaded
            cumulative_downloaded = downloaded
            
        elif is_audio_file:
            progress_info['audio']['downloaded'] = downloaded
            cumulative_downloaded = progress_info['video']['total'] + downloaded
        else:
            cumulative_downloaded = downloaded

        video_total = progress_info['video']['total']
        audio_total = progress_info['audio']['total']
        audio_est = progress_info.get('audio_size_est', 0)
        
        if audio_total <= 0 and audio_est > 0:
            current_total_plan = video_total + audio_est
        else:
            current_total_plan = video_total + audio_total
        
        if current_total_plan <= 0:
            current_total_plan = current_real_total if current_real_total > 0 else 1

        percent = (cumulative_downloaded / current_total_plan) * 100
        if percent > 100.0:
            percent = 100.0
        
        d['_percent_str'] = f"{percent:.1f}%"
        d['downloaded_bytes'] = cumulative_downloaded
        d['total_bytes'] = current_total_plan
        d['total_bytes_estimate'] = current_total_plan
        
        speed = d.get('speed')
        if speed:
            d['_speed_str'] = self._format_speed(speed)
        
        self.progress_updated.emit(d, task_id)

    def _handle_postprocessing_status(self, d: Dict[str, Any], status: str, task_id: int) -> None:
        """후처리/완료 상태 처리"""
        if task_id not in self.download_progress:
            return
            
        progress_info = self.download_progress[task_id]
        
        if status == 'postprocessing':
            d['_percent_str'] = "처리 중..."
            d['_speed_str'] = "변환/병합"
            
            total_size = progress_info.get('total_size_est', 0)
            if total_size > 0:
                d['downloaded_bytes'] = total_size
                d['total_bytes'] = total_size
                d['total_bytes_estimate'] = total_size
                    
        elif status == 'finished':
            import os
            current_filename = d.get('filename', '')
            clean_current = os.path.basename(current_filename)
            for ext in ['.part', '.ytdl']:
                if clean_current.endswith(ext):
                    clean_current = clean_current[:-len(ext)]
                    break

            saved_audio_name = progress_info['audio'].get('filename')
            if saved_audio_name: 
                saved_audio_name = os.path.basename(saved_audio_name)
            
            audio_total = progress_info['audio']['total']
            is_audio_file = (saved_audio_name and clean_current == saved_audio_name)
            
            if audio_total > 0 and not is_audio_file:
                return

            d['_percent_str'] = "100%"
            d['_speed_str'] = "다운로드 완료"
            
            total_size = progress_info.get('total_size_est', 0)
            if total_size > 0:
                d['downloaded_bytes'] = total_size
                d['total_bytes'] = total_size
                d['total_bytes_estimate'] = total_size
        
        self.progress_updated.emit(d, task_id)