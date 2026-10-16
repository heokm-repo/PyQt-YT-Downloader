from copy import deepcopy

import pytest
from PyQt5.QtCore import QCoreApplication, QEvent, Qt
from PyQt5.QtWidgets import QApplication, QDialog

from constants import FORMAT_OPTIONS
from gui.windows.settings_dialog import SettingsDialog
from utils.settings_store import default_settings


@pytest.fixture
def dialog():
    app = QApplication.instance() or QApplication([])
    settings = default_settings()
    settings['unknown'] = {'keep': True}
    widget = SettingsDialog(settings)
    widget.setAttribute(Qt.WA_DontShowOnScreen, True)
    widget.show()
    app.processEvents()
    yield widget
    widget.close()
    widget.deleteLater()
    QCoreApplication.sendPostedEvents(None, QEvent.DeferredDelete)


def test_tabs_keep_form_values_and_cancel_does_not_mutate_settings(dialog):
    original = deepcopy(dialog.settings)
    dialog.folder_line.setText('C:/changed')
    dialog.language_combo.setCurrentIndex(2)
    dialog.theme_combo.setCurrentIndex(1)
    for index in (2, 1, 0, 1, 2, 0):
        dialog.tab_widget.setCurrentIndex(index)
    assert dialog.folder_line.text() == 'C:/changed'
    assert dialog.theme_combo.currentIndex() == 1
    dialog.reject()
    assert dialog.result() == QDialog.Rejected
    assert dialog.settings == original


@pytest.mark.parametrize('fmt', FORMAT_OPTIONS)
def test_save_preserves_fields_and_quality_enablement_for_all_formats(dialog, fmt):
    dialog.compatibility_check.setChecked(False)
    dialog.format_combo.setCurrentText(fmt)
    audio = fmt in ('mp3', 'm4a', 'wav')
    assert dialog.quality_combo.isEnabled() == (not audio)
    assert dialog.audio_quality_combo.isEnabled() == (fmt != 'wav')
    dialog.folder_line.setText('C:/saved')
    dialog.norm_check.setChecked(True)
    dialog.accel_check.setChecked(False)
    dialog.max_downloads_spin.setValue(3)
    dialog.theme_combo.setCurrentIndex(1)
    dialog.accept()
    assert dialog.result() == QDialog.Accepted
    saved = dialog.get_new_settings()
    assert saved['format'] == fmt
    assert saved['download_folder'] == 'C:/saved'
    assert saved['normalize_audio'] is True and saved['use_acceleration'] is False
    assert saved['max_downloads'] == 3 and saved['theme'] == 'dark'
    assert saved['unknown'] == {'keep': True}


def test_compatibility_and_acceleration_callbacks_remain_connected(dialog):
    dialog.compatibility_check.setChecked(False)
    dialog.format_combo.setCurrentText('webm')
    dialog.compatibility_check.setChecked(True)
    assert dialog.format_combo.currentText() == 'mp4'
    dialog.accel_check.setChecked(False)
    assert dialog.max_downloads_spin.isEnabled()
    dialog.accel_check.setChecked(True)
    assert not dialog.max_downloads_spin.isEnabled()
