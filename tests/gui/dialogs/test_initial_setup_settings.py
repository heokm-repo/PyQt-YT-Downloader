from unittest.mock import patch

from PyQt5.QtWidgets import QApplication, QDialog

from constants import KEY_LANGUAGE
from gui.dialogs import init_setup_dialog
from locales import get_language, set_language


def test_initial_dialog_uses_snapshot_and_saves_selected_language():
    app = QApplication.instance() or QApplication([])
    previous_language = get_language()
    snapshot = {KEY_LANGUAGE: 'en', 'unknown': 'preserve'}
    dialog = None
    try:
        with patch.object(init_setup_dialog, 'load_settings') as load, patch.object(
            init_setup_dialog, 'save_settings'
        ) as save:
            dialog = init_setup_dialog.InitSetupDialog(initial_settings=snapshot)
            load.assert_not_called()
            dialog.lang_combo.setCurrentIndex(dialog.lang_combo.findData('ko'))
            dialog._on_start_clicked()
            assert dialog.result() == QDialog.Accepted
            assert save.call_args.args[0] == {KEY_LANGUAGE: 'ko', 'unknown': 'preserve'}
            assert snapshot[KEY_LANGUAGE] == 'en'
            assert get_language() == 'ko'
    finally:
        if dialog is not None:
            dialog.deleteLater()
        app.processEvents()
        set_language(previous_language)
