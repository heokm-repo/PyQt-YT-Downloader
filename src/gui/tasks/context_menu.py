"""Context-menu builder for task-card right-click menus."""
from typing import List, Dict, Callable, TYPE_CHECKING

from PyQt5.QtWidgets import QMenu, QAction
import qtawesome as qta

from locales.strings import STR
from gui.tasks.context_menu_plan import build_context_menu_visibility
from resources import colors, styles

if TYPE_CHECKING:
    from data.models import DownloadTask


class ContextMenuBuilder:
    """Builds the right-click context menu for task cards."""
    
    def __init__(self, parent_widget):
        """
        Args:
            parent_widget: Parent widget used when creating QAction objects.
        """
        self.parent = parent_widget
    
    def build(
        self,
        selected_tasks: List['DownloadTask'],
        callbacks: Dict[str, Callable]
    ) -> QMenu:
        """Build a context menu for the current task selection."""
        menu = QMenu(self.parent)
        menu.setStyleSheet(styles.TASK_CONTEXT_MENU_STYLE)
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
            self._add_action(menu, STR.MENU_PLAY, lambda: _log_and_call('play', callbacks.get('play')), 'mdi.play', colors.COLOR_SUCCESS)

        if visibility.open_folder:
            self._add_action(menu, STR.MENU_OPEN_FOLDER, lambda: _log_and_call('open_folder', callbacks.get('open_folder')), 'mdi.folder-open', colors.COLOR_INFO)

        if visibility.copy_url:
            self._add_action(menu, STR.MENU_COPY_URL, lambda: _log_and_call('copy_url', callbacks.get('copy_url')), 'mdi.content-copy', colors.COLOR_ICON_SUBDUED)

        menu.addSeparator()

        if visibility.pause:
            self._add_action(menu, f"{STR.MENU_PAUSE}{suffix}", lambda: _log_and_call('pause', callbacks.get('pause')), 'mdi.pause', colors.COLOR_ERROR)

        if visibility.resume:
            self._add_action(menu, f"{STR.MENU_RESUME}{suffix}", lambda: _log_and_call('resume', callbacks.get('resume')), 'mdi.play', colors.COLOR_SUCCESS)

        if visibility.retry:
            self._add_action(menu, f"{STR.MENU_RETRY}{suffix}", lambda: _log_and_call('retry', callbacks.get('retry')), 'mdi.refresh', colors.COLOR_WARNING)

        menu.addSeparator()

        if visibility.delete_file:
            self._add_action(menu, f"{STR.MENU_DELETE_FILE}{suffix}", lambda: _log_and_call('delete_file', callbacks.get('delete_file')), 'mdi.delete', colors.COLOR_ERROR)

        if visibility.remove:
            self._add_action(menu, f"{STR.MENU_REMOVE}{suffix}", lambda: _log_and_call('remove', callbacks.get('remove')), 'mdi.close', colors.COLOR_ICON_MUTED)

        if visibility.remove_completed:
            self._add_action(menu, STR.MENU_REMOVE_COMPLETED, lambda: _log_and_call('remove_all_completed', callbacks.get('remove_all_completed')), 'mdi.playlist-remove', colors.COLOR_ICON_MUTED)

        return menu

    def _add_action(self, menu: QMenu, text: str, callback: Callable, icon_name: str = None, icon_color: str | None = None) -> None:
        """Add an action to the menu."""
        if callback is None:
            return
        action = QAction(text, self.parent)
        if icon_name:
            action.setIcon(
                qta.icon(icon_name, color=icon_color or colors.COLOR_ICON_SUBDUED)
            )
        action.triggered.connect(callback)
        menu.addAction(action)
