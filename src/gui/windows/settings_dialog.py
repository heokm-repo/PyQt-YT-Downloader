import os
import json
import sys
import subprocess
import shutil
from PyQt5.QtWidgets import (QVBoxLayout, QHBoxLayout, QLineEdit, 
                             QPushButton, QLabel, QFormLayout, QSpinBox,
                             QComboBox, QFileDialog, QCheckBox, QTabWidget, QWidget)
from PyQt5.QtCore import Qt, QPoint
from PyQt5.QtGui import QFont, QColor, QStandardItem

from utils.utils import get_user_data_path, get_base_path
from constants import (
    KEY_DOWNLOAD_FOLDER, KEY_VIDEO_QUALITY, KEY_AUDIO_QUALITY, KEY_FORMAT,
    KEY_MAX_DOWNLOADS, KEY_NORMALIZE_AUDIO, KEY_USE_ACCELERATION, KEY_LANGUAGE,
    DEFAULT_VIDEO_QUALITY, DEFAULT_AUDIO_QUALITY, DEFAULT_FORMAT,
    DEFAULT_MAX_DOWNLOADS, DEFAULT_ACCELERATION, DEFAULT_NORMALIZE,
    FORMAT_OPTIONS, VIDEO_FORMATS, AUDIO_FORMATS,
    VIDEO_QUALITY_OPTIONS, AUDIO_QUALITY_OPTIONS,
    MAX_DOWNLOADS_RANGE,
    APP_VERSION,
    BTN_TEXT_CLOSE_X
)
from locales import DEFAULT_LANGUAGE, SUPPORTED_LANGUAGES
from locales.strings import STR
from gui.widgets.base_dialog import BaseDialog
from gui.widgets.message_dialog import MessageDialog
from resources.styles import (
    SETTINGS_CONTAINER_STYLE, SETTINGS_TITLE_LABEL_STYLE, SETTINGS_CLOSE_BUTTON_STYLE,
    SETTINGS_SECTION_LABEL_STYLE, SETTINGS_LABEL_STYLE, SETTINGS_BROWSE_BUTTON_STYLE,
    SETTINGS_INPUT_STYLE, SETTINGS_COMBO_STYLE, SETTINGS_CHECKBOX_STYLE,
    SETTINGS_CANCEL_BUTTON_STYLE, SETTINGS_SAVE_BUTTON_STYLE,
    SETTINGS_TAB_STYLE, SETTINGS_HELP_ICON_STYLE,
    SETTINGS_UPDATE_BUTTON_STYLE, SETTINGS_UNINSTALL_BUTTON_STYLE,
    # Moved Constants
    SETTINGS_DIALOG_WIDTH, SETTINGS_DIALOG_HEIGHT, SETTINGS_CONTAINER_MARGIN,
    SETTINGS_CONTENT_MARGIN, SETTINGS_CONTENT_SPACING, SETTINGS_INPUT_HEIGHT,
    SETTINGS_BUTTON_HEIGHT, SETTINGS_BUTTON_WIDTH, SETTINGS_TITLE_BAR_HEIGHT,
    SETTINGS_CLOSE_BUTTON_SIZE, SETTINGS_SHADOW_BLUR_RADIUS, SETTINGS_SHADOW_ALPHA,
    SETTINGS_FONT_FAMILY, SETTINGS_TITLE_FONT_SIZE, SETTINGS_SECTION_FONT_SIZE,
    COLOR_DIVIDER
)
from utils.logger import log


# ===== 설정 로드/저장 함수 =====

def load_settings():
    """JSON 파일에서 설정 로드"""
    settings_file = os.path.join(get_user_data_path(), 'settings.json')
    
    # 기본 설정값
    default_settings = {
        KEY_DOWNLOAD_FOLDER: os.path.join(get_base_path(), 'youtube_downloads'),
        KEY_VIDEO_QUALITY: DEFAULT_VIDEO_QUALITY,
        KEY_AUDIO_QUALITY: DEFAULT_AUDIO_QUALITY,
        KEY_FORMAT: DEFAULT_FORMAT,
        KEY_MAX_DOWNLOADS: DEFAULT_MAX_DOWNLOADS,
        KEY_NORMALIZE_AUDIO: DEFAULT_NORMALIZE,
        KEY_USE_ACCELERATION: DEFAULT_ACCELERATION,
        KEY_LANGUAGE: DEFAULT_LANGUAGE
    }
    
    try:
        if os.path.exists(settings_file):
            with open(settings_file, 'r', encoding='utf-8') as f:
                loaded_settings = json.load(f)
                default_settings.update(loaded_settings)
    except Exception as e:
        log.error(f"설정 로드 실패: {e}", exc_info=True)
    
    # 다운로드 폴더가 없으면 생성
    if not os.path.exists(default_settings[KEY_DOWNLOAD_FOLDER]):
        try:
            os.makedirs(default_settings[KEY_DOWNLOAD_FOLDER], exist_ok=True)
        except Exception as e:
            log.warning(f"다운로드 폴더 생성 실패: {e}")
            
    return default_settings


def save_settings(settings):
    """설정을 JSON 파일에 저장"""
    settings_file = os.path.join(get_user_data_path(), 'settings.json')
    try:
        with open(settings_file, 'w', encoding='utf-8') as f:
            json.dump(settings, f, ensure_ascii=False, indent=2)
    except Exception as e:
        log.error(f"설정 저장 실패: {e}", exc_info=True)


# ===== 설정 다이얼로그 클래스 =====

class SettingsDialog(BaseDialog):
    """다운로드 설정 다이얼로그"""
    
    def __init__(self, current_settings, parent=None):
        self.settings = current_settings
        
        super().__init__(
            parent=parent,
            title=STR.TITLE_SETTINGS,
            icon_text=None,
            show_close_btn=True,
            show_divider=False
        )
        
        self.resize(SETTINGS_DIALOG_WIDTH, SETTINGS_DIALOG_HEIGHT)
        
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
        """일반 설정 탭 생성"""
        layout = QVBoxLayout(parent)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)
        
        # 저장 위치
        self._create_section_label(STR.SETTINGS_SEC_LOCATION, layout)
        
        folder_layout = QHBoxLayout()
        folder_layout.setSpacing(10)
        
        self.folder_line = QLineEdit(self.settings[KEY_DOWNLOAD_FOLDER])
        self.folder_line.setReadOnly(True)
        self.folder_line.setFixedHeight(SETTINGS_INPUT_HEIGHT)
        self.folder_line.setStyleSheet(SETTINGS_INPUT_STYLE)
        
        self.browse_btn = QPushButton(STR.SETTINGS_BTN_BROWSE)
        self.browse_btn.setCursor(Qt.PointingHandCursor)
        self.browse_btn.setFixedHeight(SETTINGS_INPUT_HEIGHT)
        self.browse_btn.clicked.connect(self._browse_folder)
        self.browse_btn.setStyleSheet(SETTINGS_BROWSE_BUTTON_STYLE)
        
        folder_layout.addWidget(self.folder_line)
        folder_layout.addWidget(self.browse_btn)
        layout.addLayout(folder_layout)
        
        # 언어 선택
        self._create_section_label(STR.SETTINGS_SEC_GENERAL, layout)
        
        lang_form_layout = QFormLayout()
        lang_form_layout.setSpacing(10)
        lang_form_layout.setLabelAlignment(Qt.AlignLeft)
        
        self.language_combo = QComboBox()
        language_display = [f"{code} - {name}" for code, name in SUPPORTED_LANGUAGES.items()]
        self.language_combo.addItems(language_display)
        current_lang = self.settings.get(KEY_LANGUAGE, DEFAULT_LANGUAGE)
        if current_lang in SUPPORTED_LANGUAGES:
            lang_index = list(SUPPORTED_LANGUAGES.keys()).index(current_lang)
            self.language_combo.setCurrentIndex(lang_index)
        else:
            self.language_combo.setCurrentIndex(0)
        self.language_combo.setFixedHeight(SETTINGS_INPUT_HEIGHT)
        self.language_combo.setStyleSheet(SETTINGS_COMBO_STYLE)
        lang_form_layout.addRow(self._create_label(STR.SETTINGS_LABEL_LANGUAGE), self.language_combo)
        
        layout.addLayout(lang_form_layout)
        
        # 쿠키 (인앱 로그인)
        cookie_layout = QHBoxLayout()
        cookie_layout.setSpacing(10)
        
        cookie_label = self._create_label(STR.SETTINGS_LABEL_COOKIES)
        cookie_layout.addWidget(cookie_label)
        
        cookie_layout.addStretch()
        
        login_btn = QPushButton(STR.BTN_LOGIN)
        login_btn.setFixedSize(120, SETTINGS_INPUT_HEIGHT)
        login_btn.setCursor(Qt.PointingHandCursor)
        login_btn.setStyleSheet(SETTINGS_BROWSE_BUTTON_STYLE)
        login_btn.clicked.connect(self._on_login_clicked)
        cookie_layout.addWidget(login_btn)
        
        layout.addLayout(cookie_layout)
        layout.addStretch()

    def _create_download_tab(self, parent):
        """다운로드 설정 탭 생성"""
        layout = QVBoxLayout(parent)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)
        
        # 품질 및 포맷
        self._create_section_label(STR.SETTINGS_SEC_QUALITY, layout)
        
        grid_layout = QFormLayout()
        grid_layout.setSpacing(10)
        grid_layout.setLabelAlignment(Qt.AlignLeft)
        
        # 화질
        self.quality_combo = self._create_combo(
            VIDEO_QUALITY_OPTIONS, 
            self.settings[KEY_VIDEO_QUALITY]
        )
        grid_layout.addRow(self._create_label(STR.SETTINGS_LABEL_VIDEO), self.quality_combo)
        
        # 음질
        self.audio_quality_combo = self._create_combo(
            AUDIO_QUALITY_OPTIONS,
            self.settings[KEY_AUDIO_QUALITY]
        )
        grid_layout.addRow(self._create_label(STR.SETTINGS_LABEL_AUDIO), self.audio_quality_combo)
        
        # 포맷
        self.format_combo = QComboBox()
        model = self.format_combo.model()
        
        # 헤더 폰트 설정
        header_font = QFont()
        header_font.setBold(True)
        
        # Video Section
        video_header = QStandardItem(STR.SETTINGS_HEADER_VIDEO)
        video_header.setFont(header_font)
        video_header.setTextAlignment(Qt.AlignCenter)
        video_header.setEnabled(False) 
        video_header.setBackground(QColor(COLOR_DIVIDER))
        model.appendRow(video_header)
        
        for fmt in VIDEO_FORMATS:
            self.format_combo.addItem(fmt)
            
        # Audio Section
        audio_header = QStandardItem(STR.SETTINGS_HEADER_AUDIO)
        audio_header.setFont(header_font)
        audio_header.setTextAlignment(Qt.AlignCenter)
        audio_header.setEnabled(False)
        audio_header.setBackground(QColor(COLOR_DIVIDER))
        model.appendRow(audio_header)
        
        for fmt in AUDIO_FORMATS:
            self.format_combo.addItem(fmt)
        
        current_fmt = self.settings.get(KEY_FORMAT, DEFAULT_FORMAT)
        if current_fmt in FORMAT_OPTIONS:
            self.format_combo.setCurrentText(current_fmt)
            
        self.format_combo.setFixedHeight(SETTINGS_INPUT_HEIGHT)
        self.format_combo.setStyleSheet(SETTINGS_COMBO_STYLE)
        grid_layout.addRow(self._create_label(STR.SETTINGS_LABEL_FORMAT), self.format_combo)
        
        # 최대 동시 다운로드 수
        self.max_downloads_spin = QSpinBox()
        self.max_downloads_spin.setRange(*MAX_DOWNLOADS_RANGE)
        self.max_downloads_spin.setValue(
            int(self.settings.get(KEY_MAX_DOWNLOADS, DEFAULT_MAX_DOWNLOADS))
        )
        self.max_downloads_spin.setFixedHeight(SETTINGS_INPUT_HEIGHT)
        self.max_downloads_spin.setStyleSheet(SETTINGS_INPUT_STYLE)
        grid_layout.addRow(self._create_label(STR.SETTINGS_LABEL_MAX_DL), self.max_downloads_spin)
        
        layout.addLayout(grid_layout)
        
        # 고급 기능
        self._create_section_label(STR.SETTINGS_SEC_ADVANCED, layout)
        
        # 음량 평준화
        norm_tooltip = STR.TOOLTIP_NORMALIZE
        self.norm_check = QCheckBox()
        self.norm_check.setChecked(self.settings.get(KEY_NORMALIZE_AUDIO, DEFAULT_NORMALIZE))
        self.norm_check.setStyleSheet(SETTINGS_CHECKBOX_STYLE)
        
        self._create_option_row(layout, STR.SETTINGS_CHK_NORMALIZE, norm_tooltip, self.norm_check)

        # 다운로드 가속
        accel_tooltip = STR.TOOLTIP_ACCEL
        self.accel_check = QCheckBox()
        self.accel_check.setChecked(self.settings.get(KEY_USE_ACCELERATION, DEFAULT_ACCELERATION))
        self.accel_check.stateChanged.connect(lambda state: self._on_acceleration_changed(state == 2))
        self.accel_check.setStyleSheet(SETTINGS_CHECKBOX_STYLE)
        
        self._create_option_row(layout, STR.SETTINGS_CHK_ACCEL, accel_tooltip, self.accel_check)
        
        # 초기 상태 반영
        self._on_acceleration_changed(self.accel_check.isChecked())
        
        layout.addStretch()

    def _create_option_row(self, parent_layout, text, tooltip, checkbox):
        """옵션 행 생성 (❔ 아이콘 / 텍스트 / 체크박스)"""
        row_layout = QHBoxLayout()
        row_layout.setSpacing(8)
        
        # 1. 물음표 아이콘
        help_icon = QLabel("❔")
        # help_icon.setToolTip(tooltip)  # 기본 툴팁 대신 커스텀 이벤트 사용
        # help_icon.setCursor(Qt.PointingHandCursor)  # 커서 변경 제거
        help_icon.setStyleSheet(SETTINGS_HELP_ICON_STYLE)
        
        # 즉시 툴팁 표시를 위한 이벤트 처리
        from PyQt5.QtWidgets import QToolTip
        
        def enter_event(event):
            QToolTip.showText(help_icon.mapToGlobal(QPoint(0, help_icon.height())), tooltip)
            
        def leave_event(event):
            QToolTip.hideText()
            
        help_icon.enterEvent = enter_event
        help_icon.leaveEvent = leave_event
        
        # 2. 라벨
        label = QLabel(text)
        label.setFont(QFont(SETTINGS_FONT_FAMILY, SETTINGS_SECTION_FONT_SIZE))
        label.setStyleSheet(SETTINGS_LABEL_STYLE)
        
        # 레이아웃 추가
        row_layout.addWidget(help_icon)
        row_layout.addWidget(label)
        row_layout.addStretch() # 라벨과 체크박스 사이 간격
        row_layout.addWidget(checkbox)
        
        parent_layout.addLayout(row_layout)


    def _create_app_manage_tab(self, parent):
        """앱 관리 탭 생성"""
        layout = QVBoxLayout(parent)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)
        
        self._create_section_label(STR.SETTINGS_SEC_APP_MANAGE, layout)
        
        # 버전 정보
        version_layout = QHBoxLayout()
        version_lbl = QLabel(STR.SETTINGS_LABEL_VERSION)
        version_lbl.setFont(QFont(SETTINGS_FONT_FAMILY, SETTINGS_SECTION_FONT_SIZE))
        
        version_val_lbl = QLabel(APP_VERSION)
        version_val_lbl.setFont(QFont(SETTINGS_FONT_FAMILY, 14, QFont.Bold))
        version_val_lbl.setStyleSheet("color: #5F428B;")
        
        version_layout.addWidget(version_lbl)
        version_layout.addWidget(version_val_lbl)
        version_layout.addStretch()
        layout.addLayout(version_layout)
        
        # 업데이트 확인 버튼
        check_update_btn = QPushButton(STR.SETTINGS_BTN_CHECK_UPDATE)
        check_update_btn.setFont(QFont(SETTINGS_FONT_FAMILY, SETTINGS_SECTION_FONT_SIZE))
        check_update_btn.setCursor(Qt.PointingHandCursor)
        check_update_btn.setFixedHeight(45)
        check_update_btn.setStyleSheet(SETTINGS_UPDATE_BUTTON_STYLE)
        check_update_btn.clicked.connect(self._on_check_update_clicked)
        layout.addWidget(check_update_btn)
        
        # 앱 삭제 버튼
        uninstall_btn = QPushButton(STR.SETTINGS_BTN_UNINSTALL)
        uninstall_btn.setFont(QFont(SETTINGS_FONT_FAMILY, SETTINGS_SECTION_FONT_SIZE))
        uninstall_btn.setCursor(Qt.PointingHandCursor)
        uninstall_btn.setFixedHeight(45)
        uninstall_btn.setStyleSheet(SETTINGS_UNINSTALL_BUTTON_STYLE)
        uninstall_btn.clicked.connect(self._on_uninstall_clicked)
        layout.addWidget(uninstall_btn)
        
        layout.addStretch()

    def _create_button_section(self):
        """하단 버튼 섹션 생성"""
        # BaseDialog 의 button_layout 을 사용
        
        cancel_btn = QPushButton(STR.BTN_CANCEL)
        cancel_btn.setFixedSize(SETTINGS_BUTTON_WIDTH, SETTINGS_BUTTON_HEIGHT)
        cancel_btn.setCursor(Qt.PointingHandCursor)
        cancel_btn.clicked.connect(self.reject)
        cancel_btn.setStyleSheet(SETTINGS_CANCEL_BUTTON_STYLE)
        
        save_btn = QPushButton(STR.BTN_SAVE)
        save_btn.setFixedSize(SETTINGS_BUTTON_WIDTH, SETTINGS_BUTTON_HEIGHT)
        save_btn.setCursor(Qt.PointingHandCursor)
        save_btn.clicked.connect(self.accept)
        save_btn.setStyleSheet(SETTINGS_SAVE_BUTTON_STYLE)
        
        self.button_layout.addWidget(cancel_btn)
        self.button_layout.addWidget(save_btn)

    # ===== 헬퍼 메서드 =====
    
    def _create_section_label(self, text, layout):
        """섹션 타이틀 라벨 생성"""
        lbl = QLabel(text)
        lbl.setFont(QFont(SETTINGS_FONT_FAMILY, SETTINGS_SECTION_FONT_SIZE, QFont.Bold))
        lbl.setStyleSheet(SETTINGS_SECTION_LABEL_STYLE)
        layout.addWidget(lbl)
        
    def _create_label(self, text):
        """일반 라벨 생성"""
        lbl = QLabel(text)
        lbl.setFont(QFont(SETTINGS_FONT_FAMILY, SETTINGS_SECTION_FONT_SIZE))
        lbl.setStyleSheet(SETTINGS_LABEL_STYLE)
        return lbl
    
    def _create_combo(self, items, current_value):
        """스타일이 적용된 콤보박스 생성"""
        combo = QComboBox()
        combo.addItems(items)
        combo.setCurrentText(current_value)
        combo.setFixedHeight(SETTINGS_INPUT_HEIGHT)
        combo.setStyleSheet(SETTINGS_COMBO_STYLE)
        return combo

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
        if checked:
            # 다운로드 가속이 켜지면 최대 다운로드 수를 1로 고정하고 비활성화
            self.max_downloads_spin.setValue(1)
            self.max_downloads_spin.setEnabled(False)
        else:
            # 다운로드 가속이 꺼지면 최대 다운로드 수 편집 가능
            self.max_downloads_spin.setEnabled(True)
    
    def _on_login_clicked(self):
        """인앱 로그인 버튼 클릭 시 호출"""
        try:
            from gui.windows.login_browser import LoginBrowser
            dialog = LoginBrowser(self)
            dialog.exec_()
        except ImportError:
            log.error("LoginBrowser module not available (PyQtWebEngine required)")
        except Exception as e:
            log.error(f"Login browser error: {e}", exc_info=True)

    # ===== 다이얼로그 결과 처리 =====
    
    def accept(self):
        """저장 버튼 클릭 시 설정 저장"""
        folder_path = self.folder_line.text().strip()
        
        # 폴더 경로 유효성 검사
        # 폴더 경로 유효성 검사
        # 폴더 경로 유효성 검사
        if not folder_path:
            MessageDialog(STR.TITLE_ERROR, STR.ERR_SETTINGS_NO_FOLDER, MessageDialog.WARNING, self).exec_()
            return
        
        # 폴더가 없으면 생성 시도
        if not os.path.exists(folder_path):
            try:
                os.makedirs(folder_path, exist_ok=True)
            except Exception as e:
                MessageDialog(STR.TITLE_ERROR, 
                              STR.ERR_SETTINGS_CREATE_FOLDER.format(error=str(e)),
                              MessageDialog.WARNING, self).exec_()
                return
        
        # 폴더가 디렉토리가 아닌 경우
        if not os.path.isdir(folder_path):
            MessageDialog(STR.TITLE_ERROR, STR.ERR_SETTINGS_INVALID_FOLDER, MessageDialog.WARNING, self).exec_()
            return
        
        # 설정값 업데이트
        self.settings[KEY_DOWNLOAD_FOLDER] = folder_path
        self.settings[KEY_VIDEO_QUALITY] = self.quality_combo.currentText()
        self.settings[KEY_AUDIO_QUALITY] = self.audio_quality_combo.currentText()
        self.settings[KEY_FORMAT] = self.format_combo.currentText()
        self.settings[KEY_NORMALIZE_AUDIO] = self.norm_check.isChecked()
        self.settings[KEY_USE_ACCELERATION] = self.accel_check.isChecked()
        self.settings[KEY_MAX_DOWNLOADS] = self.max_downloads_spin.value()
        
        # 언어 설정 저장
        selected_lang_index = self.language_combo.currentIndex()
        selected_lang = list(SUPPORTED_LANGUAGES.keys())[selected_lang_index]
        old_lang = self.settings.get(KEY_LANGUAGE, DEFAULT_LANGUAGE)
        self.settings[KEY_LANGUAGE] = selected_lang
        
        save_settings(self.settings)
        super().accept()
        
    def get_new_settings(self):
        """변경된 설정 반환"""
        return self.settings
    
    # ===== 앱 관리 기능 =====
    
    def _on_uninstall_clicked(self):
        """앱 삭제 버튼 클릭 시 호출"""
        # 확인 다이얼로그 표시
        dialog = MessageDialog(STR.TITLE_UNINSTALL, STR.MSG_UNINSTALL_CONFIRM, 
                               MessageDialog.QUESTION, self, show_cancel=False)
        
        if dialog.exec_() == QDialog.Accepted:
            # 개발 환경 체크
            if not getattr(sys, 'frozen', False):
                MessageDialog(STR.TITLE_SETTINGS, STR.MSG_DEV_NO_UNINSTALL, 
                              MessageDialog.INFO, self).exec_()
                log.info("개발 환경: 앱 삭제 시뮬레이션")
                return
            
            try:
                from utils.app_uninstaller import uninstall_app
                
                # 앱 삭제 실행
                if uninstall_app():
                    # 앱 종료
                    from PyQt5.QtWidgets import QApplication
                    QApplication.quit()
                else:
                    MessageDialog(STR.TITLE_UNINSTALL_ERR, STR.ERR_UNINSTALL_START,
                                  MessageDialog.ERROR, self).exec_()
                
            except Exception as e:
                log.error(f"앱 삭제 중 오류 발생: {e}", exc_info=True)
                MessageDialog(STR.TITLE_UNINSTALL_ERR, STR.ERR_UNINSTALL_FAIL.format(error=str(e)),
                              MessageDialog.ERROR, self).exec_()

    
    def _on_check_update_clicked(self):
        """업데이트 확인 버튼 클릭 시 호출"""
        try:
            from utils.app_updater import check_for_updates, download_update, apply_update
            from PyQt5.QtWidgets import QProgressDialog, QApplication
            
            # 업데이트 확인
            update_available, latest_version, download_url = check_for_updates()
            
            if not update_available:
                # 이미 최신 버전
                MessageDialog(STR.TITLE_UPDATE_CHECK, STR.MSG_UPDATE_LATEST, 
                              MessageDialog.INFO, self).exec_()
                return
            
            # 업데이트 가능 - 사용자 확인
            dialog = MessageDialog(STR.TITLE_UPDATE_CHECK, 
                                   STR.MSG_UPDATE_AVAILABLE.format(current=APP_VERSION, latest=latest_version),
                                   MessageDialog.QUESTION, self, show_cancel=False)
            
            if dialog.exec_() == QDialog.Accepted:
                # 업데이트 다운로드
                progress_dialog = QProgressDialog(
                    STR.MSG_UPDATE_DL,
                    None,  # 취소 버튼 없음
                    0, 100,
                    self
                )
                progress_dialog.setWindowTitle(STR.TITLE_UPDATE_DL)
                progress_dialog.setWindowModality(Qt.WindowModal)
                progress_dialog.show()
                
                def update_progress(value):
                    progress_dialog.setValue(value)
                    QApplication.processEvents()
                
                # 다운로드 실행
                new_exe_path = download_update(download_url, update_progress)
                progress_dialog.close()
                
                if new_exe_path:
                    # 업데이트 적용
                    if apply_update(new_exe_path):
                        log.info("업데이트 적용 완료, 앱 종료 중...")
                        QApplication.quit()
                    else:
                        MessageDialog(STR.TITLE_UPDATE_CHECK, STR.ERR_UPDATE_APPLY, 
                                      MessageDialog.WARNING, self).exec_()
                else:
                    MessageDialog(STR.TITLE_UPDATE_CHECK, STR.ERR_UPDATE_DOWNLOAD, 
                                  MessageDialog.WARNING, self).exec_()
                    
        except Exception as e:
            log.error(f"업데이트 확인 중 오류: {e}", exc_info=True)
            MessageDialog(STR.TITLE_UPDATE_CHECK, STR.ERR_UPDATE_CHECK.format(error=str(e)), 
                          MessageDialog.ERROR, self).exec_()
