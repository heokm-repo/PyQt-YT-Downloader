import sys
from PyQt5.QtWidgets import QApplication, QFileDialog, QTabWidget, QWidget
from PyQt5.QtCore import QUrl
from PyQt5.QtGui import QDesktopServices, QFont

from constants import APP_VERSION, SPONSOR_URL
from locales.strings import STR
from gui.dialogs.base_dialog import BaseDialog
from gui.dialogs.messages import (
    ask_custom_question,
    ask_question,
    show_error,
    show_info,
    show_warning,
)
from gui.settings.settings_controls import create_settings_button, set_compatibility_format_mode
from gui.settings.settings_tabs import create_general_tab, create_download_tab, create_app_manage_tab
from gui.settings.settings_form_data import (
    build_settings_from_form_values,
    is_download_folder_input_valid,
    normalize_download_folder_input,
)
from gui.settings.settings_format_options import quality_control_state_for_format
from gui.settings.settings_acceleration import max_downloads_state_for_acceleration
from gui.settings.settings_button_specs import build_dialog_action_button_specs
from gui.settings.settings_app_management import (
    build_error_message,
    run_uninstall_flow,
)
from gui.settings.settings_update_check import (
    format_update_check_message,
)
from resources import styles
from resources.styles import (
    SETTINGS_DIALOG_WIDTH, SETTINGS_DIALOG_HEIGHT,
    SETTINGS_BUTTON_HEIGHT, SETTINGS_BUTTON_WIDTH_PADDING,
    SETTINGS_FONT_FAMILY, SETTINGS_TITLE_FONT_SIZE,
    MIN_SETTINGS_TAB_WIDTH
)
from utils.logger import log



class SettingsDialog(BaseDialog):
    """Download settings dialog."""

    def __init__(
        self,
        current_settings,
        parent=None,
        active_task_check=None,
        update_worker_factory=None,
    ):
        self.settings = current_settings
        self.restart_requested = False
        self._active_task_check = active_task_check or (lambda: False)
        self._update_worker_factory = update_worker_factory
        self._update_check_worker = None
        self.update_check_button = None

        super().__init__(
            parent=parent,
            title=STR.TITLE_SETTINGS,
            icon_text=None,
            show_close_btn=True,
            show_divider=False,
            resizable=False,
            window_name=None,
        )

        self.setFixedSize(SETTINGS_DIALOG_WIDTH, SETTINGS_DIALOG_HEIGHT)
        self._center_on_primary_screen()

        # Apply the settings-dialog title style.
        self.title_label.setFont(QFont(SETTINGS_FONT_FAMILY, SETTINGS_TITLE_FONT_SIZE, QFont.Bold))
        self.title_label.setStyleSheet(styles.SETTINGS_TITLE_LABEL_STYLE)

        # Set container spacing differently if needed, wait, BaseDialog handles it roughly the same

        self._setup_content()
        self.container_layout.setStretchFactor(self.content_layout, 1)
        self._create_button_section()

    def _center_on_primary_screen(self):
        """Center the fixed settings window on the primary screen."""
        screen = QApplication.primaryScreen()
        if screen is None:
            return
        self.move(screen.availableGeometry().center() - self.rect().center())

    def _setup_content(self):
        """Create and add the settings tabs."""
        # Create tab widget.
        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet(styles.SETTINGS_TAB_STYLE)
        self.tab_widget.setMinimumWidth(MIN_SETTINGS_TAB_WIDTH)

        # Tab 1: General settings.
        general_tab = QWidget()
        self._create_general_tab(general_tab)
        self.tab_widget.addTab(general_tab, STR.SETTINGS_SEC_GENERAL)

        # Tab 2: Download settings.
        download_tab = QWidget()
        self._create_download_tab(download_tab)
        self.tab_widget.addTab(download_tab, STR.SETTINGS_SEC_QUALITY)

        # Tab 3: App management.
        app_manage_tab = QWidget()
        self._create_app_manage_tab(app_manage_tab)
        self.tab_widget.addTab(app_manage_tab, STR.SETTINGS_SEC_APP_MANAGE)

        self.content_layout.addWidget(self.tab_widget)

    def _create_general_tab(self, parent):
        return create_general_tab(self, parent)

    def _create_download_tab(self, parent):
        return create_download_tab(self, parent)

    def _create_app_manage_tab(self, parent):
        return create_app_manage_tab(self, parent)

    def _create_button_section(self):
        """Create the bottom button section."""
        # Use BaseDialog button_layout.

        button_styles = {
            "cancel": styles.SETTINGS_CANCEL_BUTTON_STYLE,
            "save": styles.SETTINGS_SAVE_BUTTON_STYLE,
        }
        button_callbacks = {
            "cancel": self.reject,
            "save": self.accept,
        }
        for spec in build_dialog_action_button_specs(STR.BTN_CANCEL, STR.BTN_SAVE):
            button = create_settings_button(
                spec,
                button_styles,
                button_callbacks,
                fixed_height=SETTINGS_BUTTON_HEIGHT,
                minimum_width_padding=SETTINGS_BUTTON_WIDTH_PADDING,
            )
            self.button_layout.addWidget(button)

    # ===== Helper Methods =====



    # ===== Event Handlers =====

    # mouse drag event handled by BaseDialog

    def _browse_folder(self):
        """Open the folder picker dialog."""
        folder = QFileDialog.getExistingDirectory(
            self, STR.TITLE_FOLDER_SELECT, self.folder_line.text()
        )
        if folder:
            self.folder_line.setText(folder)

    def _on_acceleration_changed(self, checked):
        """Handle download-acceleration checkbox changes."""
        state = max_downloads_state_for_acceleration(checked)
        if state.value is not None:
            self.max_downloads_spin.setValue(state.value)
        self.max_downloads_spin.setEnabled(state.enabled)

    def _on_compatibility_changed(self, checked):
        """Allow only broadly compatible output formats while enabled."""
        set_compatibility_format_mode(self.format_combo, checked)
        self._on_format_changed(self.format_combo.currentText())

    def _on_format_changed(self, selected_format):
        """Enable only quality controls that affect the selected format."""
        state = quality_control_state_for_format(selected_format)
        self.quality_combo.setEnabled(state.video_quality_enabled)
        self.audio_quality_combo.setEnabled(state.audio_quality_enabled)

    def _on_login_clicked(self):
        """Handle in-app login button clicks."""
        try:
            from gui.windows.login_browser import LoginBrowser
            dialog = LoginBrowser(self)
            dialog.exec_()
        except ImportError:
            log.error("LoginBrowser module not available (PyQtWebEngine required)")
        except Exception as e:
            log.error(f"Login browser failed: {e}", exc_info=True)

    def _on_logout_clicked(self):
        """Delete the exported cookie file and any remaining browser storage."""
        if not ask_question(self, STR.TITLE_LOGOUT, STR.MSG_LOGOUT_CONFIRM):
            return

        from utils.cookie_store import delete_stored_login_data

        if delete_stored_login_data():
            show_info(self, STR.TITLE_LOGOUT, STR.MSG_LOGOUT_SUCCESS)
            return

        show_error(self, STR.TITLE_LOGOUT, STR.ERR_LOGOUT_FAILED)

    # ===== Dialog Result Handling =====

    def _show_license_info(self):
        """Show the license information dialog."""
        show_info(self, STR.TITLE_LICENSE, STR.MSG_LICENSE_INFO)

    def _open_sponsor_page(self):
        """Open the shared GitHub Sponsors page in the default browser."""
        if not QDesktopServices.openUrl(QUrl(SPONSOR_URL)):
            show_warning(self, STR.TITLE_SETTINGS, STR.ERR_SPONSOR_OPEN)

    def accept(self):
        """Save settings when the Save button is clicked."""
        folder_path = normalize_download_folder_input(self.folder_line.text())

        # Validate the folder path.
        if not is_download_folder_input_valid(folder_path):
            show_warning(self, STR.TITLE_ERROR, STR.ERR_SETTINGS_NO_FOLDER)
            return

        self.settings = build_settings_from_form_values(
            self.settings,
            folder_path,
            self.quality_combo.currentText(),
            self.audio_quality_combo.currentText(),
            self.format_combo.currentText(),
            self.norm_check.isChecked(),
            self.accel_check.isChecked(),
            self.max_downloads_spin.value(),
            self.language_combo.currentIndex(),
            self.compatibility_check.isChecked(),
            self.theme_combo.currentIndex(),
        )

        self._detach_update_check_worker()
        super().accept()

    def reject(self):
        """Close the dialog without allowing a background result to reopen UI."""
        self._detach_update_check_worker()
        super().reject()

    def closeEvent(self, event):
        """Detach any in-flight update check before the dialog is closed."""
        self._detach_update_check_worker()
        super().closeEvent(event)

    def get_new_settings(self):
        """Return changed settings."""
        return self.settings

    # ===== App Management =====

    def _confirm_uninstall(self):
        """Ask whether the app should be uninstalled."""
        return ask_question(self, STR.TITLE_UNINSTALL, STR.MSG_UNINSTALL_CONFIRM)

    def _on_uninstall_clicked(self):
        """Handle the uninstall button click."""
        try:
            def start_uninstall():
                from utils.app_uninstaller import uninstall_app
                return uninstall_app()

            result = run_uninstall_flow(
                self._confirm_uninstall,
                getattr(sys, "frozen", False),
                start_uninstall,
                STR.MSG_DEV_NO_UNINSTALL,
                STR.ERR_UNINSTALL_START,
            )

            if result.cancelled:
                return

            if result.development_message:
                show_info(self, STR.TITLE_SETTINGS, result.development_message)
                log.info("Development environment: uninstall skipped.")
                return

            if result.should_quit:
                from PyQt5.QtWidgets import QApplication
                QApplication.quit()
                return

            show_error(self, STR.TITLE_UNINSTALL_ERR, result.error_message)

        except Exception as e:
            log.error(f"Uninstall failed: {e}", exc_info=True)
            show_error(
                self,
                STR.TITLE_UNINSTALL_ERR,
                build_error_message(STR.ERR_UNINSTALL_FAIL, e),
            )

    def _on_check_update_clicked(self):
        """Start a non-blocking update check."""
        worker = self._update_check_worker
        if worker is not None and worker.isRunning():
            log.info("Settings update check is already running")
            return

        try:
            if self._update_worker_factory is None:
                from gui.settings.settings_update_worker import SettingsUpdateWorker

                worker_factory = SettingsUpdateWorker
            else:
                worker_factory = self._update_worker_factory

            worker = worker_factory(
                APP_VERSION,
                parent=QApplication.instance(),
            )
            self._update_check_worker = worker
            worker.completed.connect(self._on_update_check_completed)
            worker.failed.connect(self._on_update_check_failed)
            worker.finished.connect(self._on_update_check_worker_finished)
            worker.finished.connect(worker.deleteLater)
            self._set_update_check_busy(True)
            worker.start()
        except Exception as exc:
            self._detach_update_check_worker()
            self._on_update_check_failed(str(exc) or exc.__class__.__name__)

    def _on_update_check_completed(self, summary):
        """Show the result delivered by the background update worker."""
        self._set_update_check_busy(False)
        if not summary.update_available:
            show_info(
                self,
                STR.TITLE_UPDATE_CHECK,
                STR.MSG_UPDATE_ALL_LATEST,
            )
            return

        message = format_update_check_message(
            summary,
            STR.MSG_UPDATE_COMPONENTS,
            STR.MSG_UPDATE_COMPONENT_MISSING,
            STR.MSG_UPDATE_RESTART_REQUIRED,
            STR.MSG_UPDATE_RESTART_ACTIVE_TASKS,
            bool(self._active_task_check()),
        )
        choice = ask_custom_question(
            self,
            STR.TITLE_UPDATE_CHECK,
            message,
            [
                {"text": STR.BTN_LATER, "role": "reject"},
                {"text": STR.BTN_RESTART_NOW, "role": "accept"},
            ],
        )
        if choice == 1:
            self.restart_requested = True
            self.reject()

    def _on_update_check_failed(self, error_message):
        """Restore the UI and surface a failed update check."""
        self._set_update_check_busy(False)
        log.error(f"Update check failed: {error_message}")
        show_error(
            self,
            STR.TITLE_UPDATE_CHECK,
            build_error_message(STR.ERR_UPDATE_CHECK, error_message),
        )

    def _on_update_check_worker_finished(self):
        """Release the completed worker while keeping the button usable."""
        worker = self.sender()
        if worker is not self._update_check_worker:
            return
        self._update_check_worker = None
        self._set_update_check_busy(False)

    def _set_update_check_busy(self, busy):
        """Reflect update-check state on the settings button."""
        if self.update_check_button is None:
            return
        self.update_check_button.setEnabled(not busy)
        self.update_check_button.setText(
            STR.MSG_CHECKING_INFO if busy else STR.SETTINGS_BTN_CHECK_UPDATE
        )

    def _detach_update_check_worker(self):
        """Disconnect this dialog from an in-flight app-owned worker."""
        worker = self._update_check_worker
        if worker is None:
            self._set_update_check_busy(False)
            return

        for signal, slot in (
            (worker.completed, self._on_update_check_completed),
            (worker.failed, self._on_update_check_failed),
            (worker.finished, self._on_update_check_worker_finished),
        ):
            try:
                signal.disconnect(slot)
            except TypeError as exc:
                log.debug(f"Update worker signal was already disconnected: {exc}")

        self._update_check_worker = None
        self._set_update_check_busy(False)
