from unittest.mock import Mock, patch

from PyQt5.QtCore import QRect

from gui.windowing import window_state_manager as states


def test_restore_uses_loaded_snapshot_without_another_read():
    geometry = {'x': 10, 'y': 20, 'width': 800, 'height': 600, 'maximized': True}
    window = Mock()
    with patch.object(states, 'read_settings_values') as read, patch.object(
        states, '_is_visible_on_any_screen', return_value=True
    ):
        state = states.load_window_state('MainWindow', {'window_states': {'MainWindow': geometry}})
        assert states.restore_window_state('MainWindow', window, 400, 300, state=state)
    read.assert_not_called()
    window.setGeometry.assert_called_once_with(10, 20, 800, 600)
    window.showMaximized.assert_called_once_with()


def test_absent_snapshot_state_does_not_trigger_fallback_read():
    window = Mock()
    with patch.object(states, 'read_settings_values') as read, patch.object(states, '_center_window') as center:
        assert not states.restore_window_state('MainWindow', window, 400, 300, state=None)
    read.assert_not_called()
    center.assert_called_once_with(window, 400, 300)


def test_offscreen_state_keeps_existing_centering_policy():
    window = Mock()
    with patch.object(states, '_is_visible_on_any_screen', return_value=False), patch.object(
        states, '_center_window'
    ) as center:
        assert not states.restore_window_state('MainWindow', window, 400, 300, state={'x': -10000})
    center.assert_called_once_with(window, 400, 300)
    window.setGeometry.assert_not_called()


def test_maximized_window_saves_normal_geometry_as_partial_update():
    window = Mock()
    window.isMaximized.return_value = True
    window.normalGeometry.return_value = QRect(10, 20, 800, 600)
    with patch.object(states, 'update_settings') as update:
        states.save_window_state('MainWindow', window)
    update.assert_called_once_with({'window_states': {'MainWindow': {
        'x': 10, 'y': 20, 'width': 800, 'height': 600, 'maximized': True}}})
    window.geometry.assert_not_called()
