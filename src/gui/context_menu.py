"""
컨텍스트 메뉴 빌더 클래스
우클릭 메뉴 구성 로직을 담당
"""
from typing import List, Dict, Callable, TYPE_CHECKING

from PyQt5.QtWidgets import QMenu, QAction

from constants import TaskStatus

if TYPE_CHECKING:
    from data.models import DownloadTask


class ContextMenuBuilder:
    """
    작업 카드 우클릭 컨텍스트 메뉴를 구성하는 클래스
    """
    
    def __init__(self, parent_widget):
        """
        Args:
            parent_widget: 메뉴의 부모 위젯 (QAction 생성 시 필요)
        """
        self.parent = parent_widget
    
    def build(
        self, 
        selected_tasks: List['DownloadTask'],
        callbacks: Dict[str, Callable]
    ) -> QMenu:
        """
        컨텍스트 메뉴 구성
        
        Args:
            selected_tasks: 선택된 DownloadTask 리스트
            callbacks: 콜백 함수 딕셔너리 (키: 액션명, 값: 콜백 함수)
                - 'play': 파일 실행
                - 'open_folder': 폴더 열기
                - 'pause': 일시정지
                - 'resume': 이어받기
                - 'retry': 재시도
                - 'delete_file': 파일 삭제
                - 'remove': 목록에서 제거
        
        Returns:
            구성된 QMenu 객체
        """
        menu = QMenu(self.parent)
        count = len(selected_tasks)
        suffix = f" ({count}개)" if count > 1 else ""
        
        # 상태 플래그 계산
        status_flags = self._get_status_flags(selected_tasks)
        
        # 재생 (완료된 단일 항목)
        if status_flags['finished'] and count == 1:
            self._add_action(menu, "▶ 재생", callbacks.get('play'))
        
        # 폴더 열기
        if status_flags['finished']:
            self._add_action(menu, f"📂 폴더 열기{suffix}", callbacks.get('open_folder'))
        
        menu.addSeparator()
        
        # 일시정지
        if status_flags['downloading'] or status_flags['waiting']:
            self._add_action(menu, f"⏸ 일시정지{suffix}", callbacks.get('pause'))
        
        # 이어받기
        if status_flags['paused']:
            self._add_action(menu, f"▶ 이어받기{suffix}", callbacks.get('resume'))
        
        # 재시도
        if status_flags['failed']:
            self._add_action(menu, f"↻ 재시도{suffix}", callbacks.get('retry'))
        
        menu.addSeparator()
        
        # 파일 삭제
        if status_flags['finished']:
            self._add_action(menu, f"🗑️ 파일 삭제{suffix}", callbacks.get('delete_file'))
        
        # 목록에서 제거
        self._add_action(menu, f"❌ 목록에서 제거{suffix}", callbacks.get('remove'))
        
        return menu
    
    def _get_status_flags(self, tasks: List['DownloadTask']) -> Dict[str, bool]:
        """작업 목록에서 상태 플래그 추출"""
        return {
            'finished': any(t.status == TaskStatus.FINISHED for t in tasks),
            'paused': any(t.status == TaskStatus.PAUSED for t in tasks),
            'downloading': any(t.status == TaskStatus.DOWNLOADING for t in tasks),
            'waiting': any(t.status == TaskStatus.WAITING for t in tasks),
            'failed': any(t.status == TaskStatus.FAILED for t in tasks),
        }
    
    def _add_action(self, menu: QMenu, text: str, callback: Callable) -> None:
        """메뉴에 액션 추가"""
        if callback is None:
            return
        action = QAction(text, self.parent)
        action.triggered.connect(callback)
        menu.addAction(action)
