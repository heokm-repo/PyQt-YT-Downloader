"""
다운로드 스케줄러
워커 스레드 풀과 다운로드 큐를 관리하는 클래스
main_window.py에서 분리하여 관심사 분리 (SRP)
"""
import threading
import queue

from PyQt5.QtCore import QObject, pyqtSignal

from core.workers import DownloadWorker
from utils.logger import log
from constants import WORKER_CLEANUP_WAIT_MS, SCHEDULER_PRIORITY_NORMAL


class DownloadScheduler(QObject):
    """
    다운로드 워커 스레드 풀과 큐를 관리하는 스케줄러
    
    역할:
    - 워커 스레드 생성/삭제/관리
    - 다운로드 큐 관리
    - 일시정지/재개 제어
    - 워커 시그널을 메인 윈도우로 중계
    """
    
    # 메인 윈도우로 중계할 시그널
    progress_updated = pyqtSignal(dict, int)  # 진행률, task_id
    download_finished = pyqtSignal(bool, str, int, str)  # 성공여부, 메시지, task_id, 파일경로
    task_started = pyqtSignal(int)  # task_id
    metadata_fetched = pyqtSignal(int, dict)  # task_id, metadata
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 다운로드 큐 (우선순위 큐)
        self.download_queue = queue.PriorityQueue()
        
        # 스레드 제어 이벤트
        self.stop_event = threading.Event()
        self.pause_event = threading.Event()
        self.pause_event.set()  # 기본값은 실행 상태
        
        # 워커 리스트
        self.workers = []
        
        # 개별 작업 일시정지 플래그 (task_id -> bool) - 스레드 안전을 위한 Lock 추가
        self.task_paused_flags = {}
        self._paused_flags_lock = threading.Lock()
    
    def initialize(self, max_workers: int):
        """스케줄러 초기화 및 워커 시작"""
        self.stop_event.clear()
        self.adjust_worker_count(max_workers)
    
    def add_task(self, priority: int, task_id: int, url: str, settings: dict, metadata: dict = None):
        """다운로드 큐에 작업 추가"""
        if metadata is None:
            metadata = {}
        self.download_queue.put((priority, task_id, url, settings, metadata))
    
    def pause_all(self):
        """모든 다운로드 일시정지"""
        self.pause_event.clear()
    
    def resume_all(self):
        """모든 다운로드 재개"""
        self.pause_event.set()
    
    def is_paused(self) -> bool:
        """전체 일시정지 상태인지 확인"""
        return not self.pause_event.is_set()
    
    def pause_task(self, task_id: int):
        """개별 작업 일시정지 플래그 설정 (스레드 안전)"""
        with self._paused_flags_lock:
            self.task_paused_flags[task_id] = True
    
    def resume_task(self, task_id: int):
        """개별 작업 일시정지 플래그 해제 (스레드 안전)"""
        with self._paused_flags_lock:
            if task_id in self.task_paused_flags:
                del self.task_paused_flags[task_id]
    
    def is_task_paused(self, task_id: int) -> bool:
        """개별 작업이 일시정지 상태인지 확인 (스레드 안전)"""
        with self._paused_flags_lock:
            return self.task_paused_flags.get(task_id, False)
    
    def adjust_worker_count(self, target_count: int):
        """
        워커 스레드 수를 동적으로 조절
        - 늘릴 때: 새로운 워커 추가 생성
        - 줄일 때: '우아한 퇴장(retire_flag)'을 사용하여 현재 작업 완료 후 종료
        """
        # 이미 종료된 워커들을 리스트에서 정리
        self.workers = [w for w in self.workers if w.isRunning()]
        
        current_count = len(self.workers)
        
        if target_count > current_count:
            # 늘려야 하는 경우: 부족한 만큼 추가 생성
            needed = target_count - current_count
            log.info(f"워커 {needed}명 증원 (현재 {current_count} -> 목표 {target_count})")
            
            for _ in range(needed):
                worker = DownloadWorker(
                    self.download_queue, 
                    self.stop_event, 
                    self.pause_event, 
                    self  # 스케줄러를 parent로 전달
                )
                # 워커 시그널을 스케줄러 시그널로 연결 (중계)
                worker.progress_updated.connect(self.progress_updated)
                worker.download_finished.connect(self._on_download_finished)
                worker.task_started.connect(self.task_started)
                worker.metadata_fetched.connect(self.metadata_fetched)
                worker.start()
                self.workers.append(worker)
                
        elif target_count < current_count:
            # 줄여야 하는 경우: 초과된 워커에게 퇴근(retire) 명령
            to_retire = current_count - target_count
            log.info(f"워커 {to_retire}명 감원 예약 (현재 {current_count} -> 목표 {target_count})")
            
            for _ in range(to_retire):
                if self.workers:
                    worker = self.workers.pop()
                    worker.retire_flag = True
    
    def _on_download_finished(self, success: bool, message: str, task_id: int, final_path: str):
        """다운로드 완료 시 죽은 워커 정리 후 시그널 중계"""
        # 죽은 스레드 정리
        self.workers = [w for w in self.workers if w.isRunning()]
        # 시그널 중계
        self.download_finished.emit(success, message, task_id, final_path)
    
    def get_worker_count(self) -> int:
        """현재 활성 워커 수 반환"""
        self.workers = [w for w in self.workers if w.isRunning()]
        return len(self.workers)
    
    def shutdown(self):
        """스케줄러 종료 - 모든 워커 정리"""
        # 전체 종료 신호 전송
        self.stop_event.set()
        
        # 워커에게 종료 신호 전송 (큐에 종료 마커 추가)
        for _ in self.workers:
            self.download_queue.put((SCHEDULER_PRIORITY_NORMAL, None))
        
        # 워커들이 정리할 시간을 줌
        for worker in self.workers:
            if worker.isRunning():
                worker.wait(WORKER_CLEANUP_WAIT_MS)
        
        self.workers.clear()
