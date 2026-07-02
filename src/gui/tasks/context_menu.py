"""
컨텍스트 메뉴 빌더 클래스
우클릭 메뉴 구성 로직을 담당
"""
from typing import List, Dict, Callable, TYPE_CHECKING

from PyQt5.QtWidgets import QMenu, QAction
import qtawesome as qta

from locales.strings import STR
from gui.tasks.context_menu_plan import build_context_menu_visibility

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
        """Build a context menu for the current task selection."""
        menu = QMenu(self.parent)
        count = len(selected_tasks)
        suffix = f" ({count}개)" if count > 1 else ""
        visibility = build_context_menu_visibility(
            selected_tasks,
            getattr(self.parent, 'tasks', None),
        )

        from utils.logger import log

        def _log_and_call(action_name, callback):
            if callback:
                log.debug(f"Context Menu Action: {action_name}")
                callback()

        if visibility.play:
            self._add_action(menu, STR.MENU_PLAY, lambda: _log_and_call('play', callbacks.get('play')), 'mdi.play', '#4CAF50')

        if visibility.open_folder:
            self._add_action(menu, STR.MENU_OPEN_FOLDER, lambda: _log_and_call('open_folder', callbacks.get('open_folder')), 'mdi.folder-open', '#2196F3')

        if visibility.copy_url:
            self._add_action(menu, STR.MENU_COPY_URL, lambda: _log_and_call('copy_url', callbacks.get('copy_url')), 'mdi.content-copy', '#666666')

        menu.addSeparator()

        if visibility.pause:
            self._add_action(menu, f"{STR.MENU_PAUSE}{suffix}", lambda: _log_and_call('pause', callbacks.get('pause')), 'mdi.pause', '#F44336')

        if visibility.resume:
            self._add_action(menu, f"{STR.MENU_RESUME}{suffix}", lambda: _log_and_call('resume', callbacks.get('resume')), 'mdi.play', '#4CAF50')

        if visibility.retry:
            self._add_action(menu, f"{STR.MENU_RETRY}{suffix}", lambda: _log_and_call('retry', callbacks.get('retry')), 'mdi.refresh', '#FF9800')

        menu.addSeparator()

        if visibility.delete_file:
            self._add_action(menu, f"{STR.MENU_DELETE_FILE}{suffix}", lambda: _log_and_call('delete_file', callbacks.get('delete_file')), 'mdi.delete', '#F44336')

        if visibility.remove:
            self._add_action(menu, f"{STR.MENU_REMOVE}{suffix}", lambda: _log_and_call('remove', callbacks.get('remove')), 'mdi.close', '#999999')

        if visibility.remove_completed:
            self._add_action(menu, STR.MENU_REMOVE_COMPLETED, lambda: _log_and_call('remove_all_completed', callbacks.get('remove_all_completed')), 'mdi.playlist-remove', '#999999')

        return menu

    def _add_action(self, menu: QMenu, text: str, callback: Callable, icon_name: str = None, icon_color: str = '#666666') -> None:
        """메뉴에 액션 추가"""
        if callback is None:
            return
        action = QAction(text, self.parent)
        if icon_name:
            action.setIcon(qta.icon(icon_name, color=icon_color))
        action.triggered.connect(callback)
        menu.addAction(action)
