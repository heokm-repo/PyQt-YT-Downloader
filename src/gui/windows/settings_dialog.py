import sys
from PyQt5.QtWidgets import (QVBoxLayout,
                             QFormLayout,
                             QFileDialog, QTabWidget, QWidget)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

from constants import (
    KEY_DOWNLOAD_FOLDER, KEY_VIDEO_QUALITY, KEY_AUDIO_QUALITY, KEY_FORMAT,
    KEY_MAX_DOWNLOADS, KEY_NORMALIZE_AUDIO, KEY_USE_ACCELERATION, KEY_LANGUAGE,
    DEFAULT_MAX_DOWNLOADS, DEFAULT_ACCELERATION, DEFAULT_NORMALIZE,
    VIDEO_QUALITY_OPTIONS, AUDIO_QUALITY_OPTIONS,
    APP_VERSION
)
from locales.strings import STR
from gui.dialogs.base_dialog import BaseDialog
from gui.dialogs.messages import ask_question, show_error, show_info, show_warning
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
    create_version_row,
)
from gui.settings.settings_form_data import (
    build_settings_from_form_values,
    is_download_folder_input_valid,
    normalize_download_folder_input,
)
from gui.settings.settings_acceleration import max_downloads_state_for_acceleration
from gui.settings.settings_button_specs import (
    build_app_management_button_specs,
    build_dialog_action_button_specs,
)
from gui.settings.settings_app_management import (
    build_error_message,
    run_uninstall_flow,
    run_update_flow,
)
from resources.styles import (
    SETTINGS_TITLE_LABEL_STYLE,
    SETTINGS_CANCEL_BUTTON_STYLE, SETTINGS_SAVE_BUTTON_STYLE,
    SETTINGS_TAB_STYLE,
    SETTINGS_UPDATE_BUTTON_STYLE, SETTINGS_UNINSTALL_BUTTON_STYLE,
    # Moved Constants
    SETTINGS_DIALOG_WIDTH, SETTINGS_DIALOG_HEIGHT,
    SETTINGS_BUTTON_HEIGHT, SETTINGS_BUTTON_WIDTH,
    SETTINGS_FONT_FAMILY, SETTINGS_TITLE_FONT_SIZE,
    MIN_SETTINGS_TAB_WIDTH
)
from utils.logger import log



class SettingsDialog(BaseDialog):
    """다운로드 설정 다이얼로그"""

    def __init__(self, current_settings, parent=None):
        self.settings = current_settings

        super().__init__(
            parent=parent,
            title=STR.TITLE_SETTINGS,
            icon_text=None,
            show_close_btn=True,
            show_divider=False,
            resizable=False,
            window_name="SettingsDialog"
        )

        # 저장된 상태 복원 (없으면 기본 크기로 화면 중앙 배치)
        self.restore_state(SETTINGS_DIALOG_WIDTH, SETTINGS_DIALOG_HEIGHT)
        self.setFixedSize(SETTINGS_DIALOG_WIDTH, SETTINGS_DIALOG_HEIGHT)

        # 설정 다이얼로그 전용 타이틀 스타일 적용
        self.title_label.setFont(QFont(SETTINGS_FONT_FAMILY, SETTINGS_TITLE_FONT_SIZE, QFont.Bold))
        self.title_label.setStyleSheet(SETTINGS_TITLE_LABEL_STYLE)

        # Set container spacing differently if needed, wait, BaseDialog handles it roughly the same

        self._setup_content()
        self._create_button_section()

    def _setup_content(self):
        """UI 설정 - 탭 위젯 등 생성 및 추가"""
        # 탭 위젯 생성
        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet(SETTINGS_TAB_STYLE)
        self.tab_widget.setMinimumWidth(MIN_SETTINGS_TAB_WIDTH)

        # 탭 1: 일반 설정 (General)
        general_tab = QWidget()
        self._create_general_tab(general_tab)
        self.tab_widget.addTab(general_tab, STR.SETTINGS_SEC_GENERAL)

        # 탭 2: 다운로드 설정 (Download)
        download_tab = QWidget()
        self._create_download_tab(download_tab)
        self.tab_widget.addTab(download_tab, STR.SETTINGS_SEC_QUALITY)

        # 탭 3: 앱 관리 (App Management)
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
        folder_layout, self.folder_line, self.browse_btn = create_folder_picker_row(
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
        )
        layout.addLayout(cookie_layout)
        layout.addStretch()

    def _create_download_tab(self, parent):
        """다운로드 설정 탭 생성"""
        layout = QVBoxLayout(parent)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)

        # 품질 및 포맷
        add_section_label(STR.SETTINGS_SEC_QUALITY, layout)

        grid_layout = QFormLayout()
        grid_layout.setSpacing(10)
        grid_layout.setLabelAlignment(Qt.AlignLeft)

        # 화질
        self.quality_combo = create_settings_combo(
            VIDEO_QUALITY_OPTIONS,
            self.settings[KEY_VIDEO_QUALITY]
        )
        grid_layout.addRow(create_settings_label(STR.SETTINGS_LABEL_VIDEO), self.quality_combo)

        # 음질
        self.audio_quality_combo = create_settings_combo(
            AUDIO_QUALITY_OPTIONS,
            self.settings[KEY_AUDIO_QUALITY]
        )
        grid_layout.addRow(create_settings_label(STR.SETTINGS_LABEL_AUDIO), self.audio_quality_combo)

        # 포맷
        self.format_combo = create_format_combo(
            self.settings.get(KEY_FORMAT),
            STR.SETTINGS_HEADER_VIDEO,
            STR.SETTINGS_HEADER_AUDIO,
        )
        grid_layout.addRow(create_settings_label(STR.SETTINGS_LABEL_FORMAT), self.format_combo)

        # 최대 동시 다운로드 수
        self.max_downloads_spin = create_max_downloads_spin(
            int(self.settings.get(KEY_MAX_DOWNLOADS, DEFAULT_MAX_DOWNLOADS))
        )
        grid_layout.addRow(create_settings_label(STR.SETTINGS_LABEL_MAX_DL), self.max_downloads_spin)

        layout.addLayout(grid_layout)

        # 고급 기능
        add_section_label(STR.SETTINGS_SEC_ADVANCED, layout)

        # 음량 평준화
        self.norm_check = create_settings_checkbox(
            self.settings.get(KEY_NORMALIZE_AUDIO, DEFAULT_NORMALIZE)
        )
        add_option_row(
            layout, STR.SETTINGS_CHK_NORMALIZE, STR.TOOLTIP_NORMALIZE, self.norm_check
        )

        # 다운로드 가속
        self.accel_check = create_settings_checkbox(
            self.settings.get(KEY_USE_ACCELERATION, DEFAULT_ACCELERATION),
            lambda state: self._on_acceleration_changed(state == 2),
        )
        add_option_row(
            layout, STR.SETTINGS_CHK_ACCEL, STR.TOOLTIP_ACCEL, self.accel_check
        )

        # 초기 상태 반영
        self._on_acceleration_changed(self.accel_check.isChecked())

        layout.addStretch()

    def _create_app_manage_tab(self, parent):
        """앱 관리 탭 생성"""
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
            "uninstall": self._on_uninstall_clicked,
        }
        for spec in build_app_management_button_specs(
            STR.SETTINGS_BTN_CHECK_UPDATE,
            STR.SETTINGS_BTN_LICENSE,
            STR.SETTINGS_BTN_UNINSTALL,
        ):
            button = create_settings_button(
                spec,
                button_styles,
                button_callbacks,
                fixed_height=45,
            )
            layout.addWidget(button)

        layout.addStretch()

    def _create_button_section(self):
        """하단 버튼 섹션 생성"""
        # BaseDialog 의 button_layout 을 사용

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
                fixed_size=(SETTINGS_BUTTON_WIDTH, SETTINGS_BUTTON_HEIGHT),
            )
            self.button_layout.addWidget(button)

    # ===== 헬퍼 메서드 =====



    # ===== 이벤트 핸들러 =====

    # mouse drag event handled by BaseDialog

    def _browse_folder(self):
        """폴더 선택 다이얼로그"""
        folder = QFileDialog.getExistingDirectory(
            self, STR.TITLE_FOLDER_SELECT, self.folder_line.text()
        )
        if folder:
            self.folder_line.setText(folder)

    def _on_acceleration_changed(self, checked):
        """다운로드 가속 체크박스 상태 변경 시 호출"""
        state = max_downloads_state_for_acceleration(checked)
        if state.value is not None:
            self.max_downloads_spin.setValue(state.value)
        self.max_downloads_spin.setEnabled(state.enabled)

    def _on_login_clicked(self):
        """인앱 로그인 버튼 클릭 시 호출"""
        try:
            from gui.windows.login_browser import LoginBrowser
            dialog = LoginBrowser(self)
            dialog.exec_()
        except ImportError:
            log.error("LoginBrowser module not available (PyQtWebEngine required)")
        except Exception as e:
            log.error(f"Login browser failed: {e}", exc_info=True)

    # ===== 다이얼로그 결과 처리 =====

    def _show_license_info(self):
        """라이선스 정보 다이얼로그 표시"""
        show_info(self, STR.TITLE_LICENSE, STR.MSG_LICENSE_INFO)

    def accept(self):
        """저장 버튼 클릭 시 설정 저장"""
        folder_path = normalize_download_folder_input(self.folder_line.text())

        # 폴더 경로 유효성 검사
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
        )

        super().accept()

    def get_new_settings(self):
        """변경된 설정 반환"""
        return self.settings

    # ===== 앱 관리 기능 =====

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

    def _confirm_update(self, update_result):
        """Ask whether the available update should be installed."""
        return ask_question(self, STR.TITLE_UPDATE_CHECK, update_result.message)

    def _download_update_with_progress(self, download_update, download_url):
        """Download an update while displaying a modal progress dialog."""
        from PyQt5.QtWidgets import QProgressDialog, QApplication

        progress_dialog = QProgressDialog(
            STR.MSG_UPDATE_DL,
            None,
            0,
            100,
            self,
        )
        progress_dialog.setWindowTitle(STR.TITLE_UPDATE_DL)
        progress_dialog.setWindowModality(Qt.WindowModal)
        progress_dialog.show()

        def update_progress(value):
            progress_dialog.setValue(value)
            QApplication.processEvents()

        try:
            return download_update(download_url, update_progress)
        finally:
            progress_dialog.close()

    def _on_check_update_clicked(self):
        """Handle update checks and update installation."""
        try:
            from utils.app_updater import check_for_updates, download_update, apply_update
            from PyQt5.QtWidgets import QApplication

            result = run_update_flow(
                check_for_updates,
                lambda url: self._download_update_with_progress(download_update, url),
                apply_update,
                self._confirm_update,
                APP_VERSION,
                STR.MSG_UPDATE_LATEST,
                STR.MSG_UPDATE_AVAILABLE,
                STR.ERR_UPDATE_DOWNLOAD,
                STR.ERR_UPDATE_APPLY,
            )

            if not result.update_available:
                show_info(self, STR.TITLE_UPDATE_CHECK, result.check_result.message)
                return

            if result.cancelled:
                return

            if result.should_quit:
                log.info("Update applied successfully; quitting application.")
                QApplication.quit()
                return

            show_warning(self, STR.TITLE_UPDATE_CHECK, result.error_message)

        except Exception as e:
            log.error(f"Update check failed: {e}", exc_info=True)
            show_error(
                self,
                STR.TITLE_UPDATE_CHECK,
                build_error_message(STR.ERR_UPDATE_CHECK, e),
            )
