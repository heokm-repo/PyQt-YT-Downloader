import sys
from PyQt5.QtWidgets import (
    QApplication,
    QFileDialog,
    QFormLayout,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)
from PyQt5.QtCore import Qt, QUrl
from PyQt5.QtGui import QDesktopServices, QFont

from constants import (
    KEY_DOWNLOAD_FOLDER, KEY_VIDEO_QUALITY, KEY_AUDIO_QUALITY, KEY_FORMAT,
    KEY_MAX_DOWNLOADS, KEY_NORMALIZE_AUDIO, KEY_USE_ACCELERATION, KEY_LANGUAGE,
    KEY_UNIVERSAL_COMPATIBILITY,
    DEFAULT_MAX_DOWNLOADS, DEFAULT_ACCELERATION, DEFAULT_NORMALIZE,
    DEFAULT_UNIVERSAL_COMPATIBILITY,
    VIDEO_QUALITY_OPTIONS, AUDIO_QUALITY_OPTIONS,
    APP_VERSION, SPONSOR_URL
)
from locales.strings import STR
from gui.dialogs.base_dialog import BaseDialog
from gui.dialogs.messages import (
    ask_custom_question,
    ask_question,
    show_error,
    show_info,
    show_warning,
)
from gui.settings.settings_general_rows import create_folder_picker_row, create_login_row
from gui.settings.settings_option_row import add_option_row
from gui.settings.settings_controls import (
    add_section_label,
    create_format_combo,
    create_language_combo,
    create_max_downloads_spin,
    create_settings_button,
    create_settings_checkbox,
    create_settings_combo,
    create_settings_label,
    set_compatibility_format_mode,
    create_version_row,
)
from gui.settings.settings_form_data import (
    build_settings_from_form_values,
    is_download_folder_input_valid,
    normalize_download_folder_input,
)
from gui.settings.settings_format_options import quality_control_state_for_format
from gui.settings.settings_acceleration import max_downloads_state_for_acceleration
from gui.settings.settings_button_specs import (
    build_app_management_button_specs,
    build_dialog_action_button_specs,
)
from gui.settings.settings_app_management import (
    build_error_message,
    run_uninstall_flow,
)
from gui.settings.settings_update_check import (
    format_update_check_message,
)
from resources.styles import (
    SETTINGS_TITLE_LABEL_STYLE,
    SETTINGS_CANCEL_BUTTON_STYLE, SETTINGS_SAVE_BUTTON_STYLE,
    SETTINGS_TAB_STYLE,
    SETTINGS_UPDATE_BUTTON_STYLE, SETTINGS_UNINSTALL_BUTTON_STYLE,
    # Moved Constants
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
            window_name="SettingsDialog"
        )

        # Restore saved state, or center at the default size.
        self.restore_state(SETTINGS_DIALOG_WIDTH, SETTINGS_DIALOG_HEIGHT)
        self.setFixedSize(SETTINGS_DIALOG_WIDTH, SETTINGS_DIALOG_HEIGHT)

        # Apply the settings-dialog title style.
        self.title_label.setFont(QFont(SETTINGS_FONT_FAMILY, SETTINGS_TITLE_FONT_SIZE, QFont.Bold))
        self.title_label.setStyleSheet(SETTINGS_TITLE_LABEL_STYLE)

        # Set container spacing differently if needed, wait, BaseDialog handles it roughly the same

        self._setup_content()
        self._create_button_section()

    def _setup_content(self):
        """Create and add the settings tabs."""
        # Create tab widget.
        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet(SETTINGS_TAB_STYLE)
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
        """Create the general settings tab."""
        layout = QVBoxLayout(parent)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)

        add_section_label(STR.SETTINGS_SEC_LOCATION, layout)
        folder_layout, self.folder_line, _ = create_folder_picker_row(
            self.settings[KEY_DOWNLOAD_FOLDER],
            STR.SETTINGS_BTN_BROWSE,
            self._browse_folder,
        )
        layout.addLayout(folder_layout)

        add_section_label(STR.SETTINGS_SEC_GENERAL, layout)
        lang_form_layout = QFormLayout()
        lang_form_layout.setSpacing(10)
        lang_form_layout.setLabelAlignment(Qt.AlignLeft)

        self.language_combo = create_language_combo(
            self.settings.get(KEY_LANGUAGE)
        )
        lang_form_layout.addRow(create_settings_label(STR.SETTINGS_LABEL_LANGUAGE), self.language_combo)
        layout.addLayout(lang_form_layout)

        cookie_layout = create_login_row(
            STR.SETTINGS_LABEL_COOKIES,
            STR.BTN_LOGIN,
            self._on_login_clicked,
            STR.BTN_LOGOUT,
            self._on_logout_clicked,
        )
        layout.addLayout(cookie_layout)
        layout.addStretch()

    def _create_download_tab(self, parent):
        """Create the download settings tab."""
        layout = QVBoxLayout(parent)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)

        # Quality and format.
        add_section_label(STR.SETTINGS_SEC_QUALITY, layout)

        grid_layout = QFormLayout()
        grid_layout.setSpacing(10)
        grid_layout.setLabelAlignment(Qt.AlignLeft)

        # Video quality.
        self.quality_combo = create_settings_combo(
            VIDEO_QUALITY_OPTIONS,
            self.settings[KEY_VIDEO_QUALITY]
        )
        grid_layout.addRow(create_settings_label(STR.SETTINGS_LABEL_VIDEO), self.quality_combo)

        # Audio quality.
        self.audio_quality_combo = create_settings_combo(
            AUDIO_QUALITY_OPTIONS,
            self.settings[KEY_AUDIO_QUALITY]
        )
        grid_layout.addRow(create_settings_label(STR.SETTINGS_LABEL_AUDIO), self.audio_quality_combo)

        # Format.
        self.format_combo = create_format_combo(
            self.settings.get(KEY_FORMAT),
            STR.SETTINGS_HEADER_VIDEO,
            STR.SETTINGS_HEADER_AUDIO,
        )
        self.format_combo.currentTextChanged.connect(self._on_format_changed)
        grid_layout.addRow(create_settings_label(STR.SETTINGS_LABEL_FORMAT), self.format_combo)

        # Maximum concurrent downloads.
        self.max_downloads_spin = create_max_downloads_spin(
            int(self.settings.get(KEY_MAX_DOWNLOADS, DEFAULT_MAX_DOWNLOADS))
        )
        grid_layout.addRow(create_settings_label(STR.SETTINGS_LABEL_MAX_DL), self.max_downloads_spin)

        layout.addLayout(grid_layout)

        # Advanced features.
        add_section_label(STR.SETTINGS_SEC_ADVANCED, layout)

        # Audio normalization.
        self.norm_check = create_settings_checkbox(
            self.settings.get(KEY_NORMALIZE_AUDIO, DEFAULT_NORMALIZE)
        )
        add_option_row(
            layout, STR.SETTINGS_CHK_NORMALIZE, STR.TOOLTIP_NORMALIZE, self.norm_check
        )

        # Universal compatibility.
        self.compatibility_check = create_settings_checkbox(
            self.settings.get(
                KEY_UNIVERSAL_COMPATIBILITY,
                DEFAULT_UNIVERSAL_COMPATIBILITY,
            ),
            lambda state: self._on_compatibility_changed(state == 2),
        )
        add_option_row(
            layout,
            STR.SETTINGS_CHK_COMPATIBILITY,
            STR.TOOLTIP_COMPATIBILITY,
            self.compatibility_check,
        )

        # Download acceleration.
        self.accel_check = create_settings_checkbox(
            self.settings.get(KEY_USE_ACCELERATION, DEFAULT_ACCELERATION),
            lambda state: self._on_acceleration_changed(state == 2),
        )
        add_option_row(
            layout, STR.SETTINGS_CHK_ACCEL, STR.TOOLTIP_ACCEL, self.accel_check
        )

        # Apply initial state.
        self._on_format_changed(self.format_combo.currentText())
        self._on_compatibility_changed(self.compatibility_check.isChecked())
        self._on_acceleration_changed(self.accel_check.isChecked())

        layout.addStretch()

    def _create_app_manage_tab(self, parent):
        """Create the app-management tab."""
        layout = QVBoxLayout(parent)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)

        add_section_label(STR.SETTINGS_SEC_APP_MANAGE, layout)

        layout.addLayout(
            create_version_row(STR.SETTINGS_LABEL_VERSION, APP_VERSION)
        )

        button_styles = {
            "update": SETTINGS_UPDATE_BUTTON_STYLE,
            "uninstall": SETTINGS_UNINSTALL_BUTTON_STYLE,
        }
        button_callbacks = {
            "check_update": self._on_check_update_clicked,
            "license": self._show_license_info,
            "sponsor": self._open_sponsor_page,
            "uninstall": self._on_uninstall_clicked,
        }
        for spec in build_app_management_button_specs(
            STR.SETTINGS_BTN_CHECK_UPDATE,
            STR.SETTINGS_BTN_LICENSE,
            STR.SETTINGS_BTN_SPONSOR,
            STR.SETTINGS_BTN_UNINSTALL,
        ):
            button = create_settings_button(
                spec,
                button_styles,
                button_callbacks,
                fixed_height=45,
            )
            if spec.action == "check_update":
                self.update_check_button = button
            layout.addWidget(button)

        layout.addStretch()

    def _create_button_section(self):
        """Create the bottom button section."""
        # Use BaseDialog button_layout.

        button_styles = {
            "cancel": SETTINGS_CANCEL_BUTTON_STYLE,
            "save": SETTINGS_SAVE_BUTTON_STYLE,
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
