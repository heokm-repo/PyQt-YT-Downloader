"""Task selection manager for single, Ctrl, and Shift selection behavior."""
from typing import List, Dict, Optional, TYPE_CHECKING

from PyQt5.QtCore import Qt

if TYPE_CHECKING:
    from gui.widgets.task_item import TaskWidget


class SelectionManager:
    """
    Manage task-card selection state.
    
    Attributes:
        selected_task_ids: Currently selected task IDs.
        last_clicked_task_id: Last clicked task ID, used for Shift selection.
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
        Handle card clicks for single, Shift, and Ctrl selection.
        
        Args:
            task_id: Clicked task ID.
            modifiers: Keyboard modifiers such as Qt.ControlModifier or Qt.ShiftModifier.
            task_widgets: Mapping from task_id to TaskWidget.
            task_layout: Task-list layout used to determine order.
        """
        if modifiers & Qt.ControlModifier:
            self._toggle_selection(task_id, task_widgets)
        elif modifiers & Qt.ShiftModifier:
            self._range_selection(task_id, task_widgets, task_layout)
        else:
            self._single_selection(task_id, task_widgets)
        
        # self.last_clicked_task_id = task_id  <-- Removed from here to prevent anchor update on Shift-click
    
    def _single_selection(
        self, 
        task_id: int, 
        task_widgets: Dict[int, 'TaskWidget']
    ) -> None:
        """Select one item after clearing the existing selection."""
        # Clear the existing selection.
        for tid in self.selected_task_ids:
            widget = task_widgets.get(tid)
            if widget:
                widget.selected = False
        self.selected_task_ids.clear()
        
        # Select the new item.
        widget = task_widgets.get(task_id)
        if widget:
            widget.selected = True
            self.selected_task_ids.append(task_id)
        
        self.last_clicked_task_id = task_id
    
    def _toggle_selection(
        self, 
        task_id: int, 
        task_widgets: Dict[int, 'TaskWidget']
    ) -> None:
        """Toggle selection for Ctrl-click."""
        widget = task_widgets.get(task_id)
        if not widget:
            return
        
        if task_id in self.selected_task_ids:
            widget.selected = False
            self.selected_task_ids.remove(task_id)
        else:
            widget.selected = True
            self.selected_task_ids.append(task_id)
        
        self.last_clicked_task_id = task_id
    
    def _range_selection(
        self, 
        task_id: int, 
        task_widgets: Dict[int, 'TaskWidget'],
        task_layout
    ) -> None:
        """Select a range for Shift-click."""
        if self.last_clicked_task_id is None:
            self._single_selection(task_id, task_widgets)
            return
        
        # Read widget order from the current layout.
        widget_order = []
        for i in range(task_layout.count()):
            item = task_layout.itemAt(i)
            if item and item.widget():
                w = item.widget()
                if hasattr(w, 'task_id'):
                    widget_order.append(w.task_id)
        
        # Find the start and end indices.
        try:
            start_idx = widget_order.index(self.last_clicked_task_id)
            end_idx = widget_order.index(task_id)
        except ValueError:
            self._single_selection(task_id, task_widgets)
            return
        
        # Normalize the range order.
        if start_idx > end_idx:
            start_idx, end_idx = end_idx, start_idx
        
        # Clear the existing selection.
        for tid in self.selected_task_ids:
            widget = task_widgets.get(tid)
            if widget:
                widget.selected = False
        self.selected_task_ids.clear()
        
        # Select every item in the range.
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
        """Select all tasks."""
        self.selected_task_ids.clear()
        for task_id, widget in task_widgets.items():
            widget.selected = True
            self.selected_task_ids.append(task_id)
    
    def clear(
        self, 
        task_widgets: Dict[int, 'TaskWidget']
    ) -> None:
        """Clear the selection."""
        for tid in self.selected_task_ids:
            widget = task_widgets.get(tid)
            if widget:
                widget.selected = False
        self.selected_task_ids.clear()
        self.last_clicked_task_id = None
    
    def remove_from_selection(self, task_id: int) -> None:
        """Remove a task_id from the selection without changing widget state."""
        if task_id in self.selected_task_ids:
            self.selected_task_ids.remove(task_id)
    
    def is_selected(self, task_id: int) -> bool:
        """Return whether a task_id is selected."""
        return task_id in self.selected_task_ids
    
    def get_selected_ids(self) -> List[int]:
        """Return a copy of selected task IDs."""
        return self.selected_task_ids[:]
