from collections import Counter
from unittest.mock import Mock

import pytest
import qtawesome as qta
from PyQt5 import sip
from PyQt5.QtCore import QCoreApplication, QEvent
from PyQt5.QtWidgets import QApplication

import locales
from constants import TaskStatus
from gui.tasks.task_button_config import get_task_button_specs
from gui.widgets.task_item import TaskWidget
from resources import colors, styles


EXPECTED = {
    TaskStatus.WAITING: ['remove'],
    TaskStatus.PAUSED: ['resume', 'remove'],
    TaskStatus.DOWNLOADING: ['pause', 'delete_file'],
    TaskStatus.FINISHED: ['play', 'open_folder', 'delete_file', 'remove'],
    TaskStatus.FAILED: ['retry', 'remove'],
}


@pytest.fixture
def card():
    app = QApplication.instance() or QApplication([])
    language, theme = locales.get_language(), colors.active_theme()
    widget = TaskWidget(42, 'video', {}, thumbnail_loader=Mock())
    yield widget
    widget.deleteLater()
    QCoreApplication.sendPostedEvents(None, QEvent.DeferredDelete)
    app.processEvents()
    locales.set_language(language)
    styles.apply_theme(theme)


@pytest.mark.parametrize('source', list(EXPECTED))
@pytest.mark.parametrize('target', list(EXPECTED))
def test_every_transition_keeps_common_buttons_and_emits_once(card, source, target):
    calls = Counter()
    for action in {a for actions in EXPECTED.values() for a in actions}:
        card._signal_for_button_action(action).connect(lambda task_id, action=action: calls.update([(action, task_id)]))
    card.set_status(source)
    old = dict(card.btn_container.buttons)
    for _ in range(5):
        card.set_status(target)
    buttons = card.btn_container.buttons
    assert [card.btn_layout.itemAt(i).widget() for i in range(card.btn_layout.count())] == [buttons[a] for a in EXPECTED[target]]
    for action in set(EXPECTED[source]) & set(EXPECTED[target]):
        assert buttons[action] is old[action]
    for action in set(EXPECTED[source]) - set(EXPECTED[target]):
        old[action].click()  # Must be inert even before deferred destruction.
    assert not calls
    for action in EXPECTED[target]:
        buttons[action].click()
    assert calls == Counter({(action, 42): 1 for action in EXPECTED[target]})
    QCoreApplication.sendPostedEvents(None, QEvent.DeferredDelete)
    assert all(sip.isdeleted(old[a]) for a in set(old) - set(buttons))


def test_language_theme_refresh_reuses_buttons_updates_tooltips_icons_and_style(card):
    card.set_status(TaskStatus.FINISHED)
    buttons = dict(card.btn_container.buttons)
    for theme in ('dark', 'light'):
        styles.apply_theme(theme)
        for language in locales.SUPPORTED_LANGUAGES:
            locales.set_language(language)
            card.apply_theme()
            assert card.btn_container.buttons == buttons
            for spec in get_task_button_specs(TaskStatus.FINISHED):
                button = buttons[spec.action]
                assert button.toolTip() == spec.tooltip
                assert button.styleSheet() == str(styles.ACTION_BUTTON_STYLE)
                assert not button.icon().isNull()
                assert button.icon().pixmap(32, 32).toImage() == qta.icon(
                    spec.icon_name, color=spec.color).pixmap(32, 32).toImage()


def test_unchanged_status_keeps_enabled_state_and_icon(card):
    card.set_status(TaskStatus.FINISHED)
    button = card.btn_container.buttons['play']
    button.setEnabled(False)
    key = button.icon().cacheKey()
    for _ in range(30):
        card.update_buttons(TaskStatus.FINISHED)
    assert card.btn_container.buttons['play'] is button
    assert not button.isEnabled() and button.icon().cacheKey() == key


def test_shared_delete_action_changes_cancel_tooltip_to_delete_tooltip(card):
    card.set_status(TaskStatus.DOWNLOADING)
    button = card.btn_container.buttons['delete_file']
    cancel_tooltip = button.toolTip()
    card.set_status(TaskStatus.FINISHED)
    assert card.btn_container.buttons['delete_file'] is button
    assert button.toolTip() != cancel_tooltip
    assert button.toolTip() == next(s.tooltip for s in get_task_button_specs(TaskStatus.FINISHED) if s.action == 'delete_file')
