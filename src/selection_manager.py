"""
작업 선택 관리 클래스
다중 선택, Shift 선택, Ctrl 선택 등 선택 관련 로직을 담당
"""
from typing import List, Dict, Optional, TYPE_CHECKING

from PyQt5.QtCore import Qt

if TYPE_CHECKING:
    from ui.task_item import TaskWidget


class SelectionManager:
    """
    작업 카드 선택 상태를 관리하는 클래스
    
    Attributes:
        selected_task_ids: 현재 선택된 task_id 목록
        last_clicked_task_id: 마지막으로 클릭한 task_id (Shift 선택용)
    """
    
    def __init__(self):
        self.selected_task_ids: List[int] = []
        self.last_clicked_task_id: Optional[int] = None
    
    def handle_click(
        self, 
        task_id: int, 
        modifiers: int, 
        task_widgets: Dict[int, 'TaskWidget'],
        task_layout
    ) -> None:
        """
        카드 클릭 처리 (단일/Shift/Ctrl 선택)
        
        Args:
            task_id: 클릭된 작업 ID
            modifiers: 키보드 modifier (Qt.ControlModifier, Qt.ShiftModifier 등)
            task_widgets: task_id -> TaskWidget 매핑 딕셔너리
            task_layout: 작업 목록 레이아웃 (순서 파악용)
        """
        if modifiers & Qt.ControlModifier:
            self._toggle_selection(task_id, task_widgets)
        elif modifiers & Qt.ShiftModifier:
            self._range_selection(task_id, task_widgets, task_layout)
        else:
            self._single_selection(task_id, task_widgets)
        
        self.last_clicked_task_id = task_id
    
    def _single_selection(
        self, 
        task_id: int, 
        task_widgets: Dict[int, 'TaskWidget']
    ) -> None:
        """단일 선택 (기존 선택 해제 후 새로 선택)"""
        # 기존 선택 모두 해제
        for tid in self.selected_task_ids:
            widget = task_widgets.get(tid)
            if widget:
                widget.selected = False
        self.selected_task_ids.clear()
        
        # 새로 선택
        widget = task_widgets.get(task_id)
        if widget:
            widget.selected = True
            self.selected_task_ids.append(task_id)
    
    def _toggle_selection(
        self, 
        task_id: int, 
        task_widgets: Dict[int, 'TaskWidget']
    ) -> None:
        """선택 토글 (Ctrl+클릭)"""
        widget = task_widgets.get(task_id)
        if not widget:
            return
        
        if task_id in self.selected_task_ids:
            widget.selected = False
            self.selected_task_ids.remove(task_id)
        else:
            widget.selected = True
            self.selected_task_ids.append(task_id)
    
    def _range_selection(
        self, 
        task_id: int, 
        task_widgets: Dict[int, 'TaskWidget'],
        task_layout
    ) -> None:
        """범위 선택 (Shift+클릭)"""
        if self.last_clicked_task_id is None:
            self._single_selection(task_id, task_widgets)
            return
        
        # 현재 레이아웃에서 위젯 순서 가져오기
        widget_order = []
        for i in range(task_layout.count()):
            item = task_layout.itemAt(i)
            if item and item.widget():
                w = item.widget()
                if hasattr(w, 'task_id'):
                    widget_order.append(w.task_id)
        
        # 시작과 끝 인덱스 찾기
        try:
            start_idx = widget_order.index(self.last_clicked_task_id)
            end_idx = widget_order.index(task_id)
        except ValueError:
            self._single_selection(task_id, task_widgets)
            return
        
        # 범위 정렬
        if start_idx > end_idx:
            start_idx, end_idx = end_idx, start_idx
        
        # 기존 선택 해제
        for tid in self.selected_task_ids:
            widget = task_widgets.get(tid)
            if widget:
                widget.selected = False
        self.selected_task_ids.clear()
        
        # 범위 내 모든 항목 선택
        for i in range(start_idx, end_idx + 1):
            tid = widget_order[i]
            widget = task_widgets.get(tid)
            if widget:
                widget.selected = True
                self.selected_task_ids.append(tid)
    
    def select_all(
        self, 
        task_widgets: Dict[int, 'TaskWidget']
    ) -> None:
        """모든 작업 선택"""
        self.selected_task_ids.clear()
        for task_id, widget in task_widgets.items():
            widget.selected = True
            self.selected_task_ids.append(task_id)
    
    def clear(
        self, 
        task_widgets: Dict[int, 'TaskWidget']
    ) -> None:
        """선택 해제"""
        for tid in self.selected_task_ids:
            widget = task_widgets.get(tid)
            if widget:
                widget.selected = False
        self.selected_task_ids.clear()
        self.last_clicked_task_id = None
    
    def remove_from_selection(self, task_id: int) -> None:
        """선택 목록에서 특정 task_id 제거 (위젯 상태 변경 없이)"""
        if task_id in self.selected_task_ids:
            self.selected_task_ids.remove(task_id)
    
    def is_selected(self, task_id: int) -> bool:
        """특정 task_id가 선택되었는지 확인"""
        return task_id in self.selected_task_ids
    
    def get_selected_count(self) -> int:
        """선택된 작업 수 반환"""
        return len(self.selected_task_ids)
    
    def get_selected_ids(self) -> List[int]:
        """선택된 task_id 목록의 복사본 반환"""
        return self.selected_task_ids[:]
