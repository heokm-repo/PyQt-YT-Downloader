"""Keep only the current task actions, reusing buttons with the same action."""
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QHBoxLayout, QWidget

from gui.widgets.buttons import set_icon
from resources import colors, styles
from resources.styles import BUTTON_SIZE


class TaskActionBar(QWidget):
    def __init__(self, task_id, signal_for_action, button_factory):
        super().__init__()
        self._task_id = task_id
        self._signal_for_action = signal_for_action
        self._button_factory = button_factory
        self.buttons = {}
        self._specs = {}
        self._style = None
        self.button_layout = QHBoxLayout(self)
        self.button_layout.setContentsMargins(0, 0, 0, 0)
        self.button_layout.setSpacing(5)
        self.button_layout.setAlignment(Qt.AlignRight | Qt.AlignTop)
        self.setStyleSheet(f'background: {colors.COLOR_TRANSPARENT}; border: none;')

    def apply_specs(self, specs):
        actions = {spec.action for spec in specs}
        for action in tuple(self.buttons):
            if action not in actions:
                button = self.buttons.pop(action)
                self._specs.pop(action)
                self.button_layout.removeWidget(button)
                button.hide()
                button.clicked.disconnect()
                button.deleteLater()
        style = str(styles.ACTION_BUTTON_STYLE)
        for index, spec in enumerate(specs):
            button = self.buttons.get(spec.action)
            old = self._specs.get(spec.action)
            if button is None:
                signal = self._signal_for_action(spec.action)
                task_id = self._task_id
                button = self._button_factory(
                    spec.icon_name, spec.tooltip,
                    lambda checked=False, signal=signal, task_id=task_id: signal.emit(task_id),
                    spec.color)
                self.buttons[spec.action] = button
            else:
                if (old.icon_name, old.color) != (spec.icon_name, spec.color):
                    set_icon(button, spec.icon_name, spec.color, (BUTTON_SIZE, BUTTON_SIZE))
                if old.tooltip != spec.tooltip:
                    button.setToolTip(spec.tooltip)
                if self._style != style:
                    button.setStyleSheet(style)
            item = self.button_layout.itemAt(index)
            if item is None or item.widget() is not button:
                self.button_layout.insertWidget(index, button)
            self._specs[spec.action] = spec
        self._style = style
