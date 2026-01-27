import os
import json
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLineEdit, 
                             QPushButton, QLabel, QFormLayout, QSpinBox,
                             QComboBox, QFileDialog, QFrame, QGraphicsDropShadowEffect,
                             QMessageBox, QCheckBox)
from PyQt5.QtCore import Qt, QPoint
from PyQt5.QtGui import QFont, QColor

from utils.utils import get_user_data_path, get_base_path
from constants import (
    KEY_DOWNLOAD_FOLDER, KEY_VIDEO_QUALITY, KEY_AUDIO_QUALITY, KEY_FORMAT,
    KEY_MAX_DOWNLOADS, KEY_NORMALIZE_AUDIO, KEY_USE_ACCELERATION, KEY_LANGUAGE,
    DEFAULT_VIDEO_QUALITY, DEFAULT_AUDIO_QUALITY, DEFAULT_FORMAT,
    DEFAULT_MAX_DOWNLOADS, DEFAULT_ACCELERATION, DEFAULT_NORMALIZE, DEFAULT_COOKIES_BROWSER, DEFAULT_LANGUAGE,
    VIDEO_QUALITY_OPTIONS, AUDIO_QUALITY_OPTIONS, FORMAT_OPTIONS, MAX_DOWNLOADS_RANGE,
    change_language, SUPPORTED_LANGUAGES,
    SETTINGS_DIALOG_WIDTH, SETTINGS_DIALOG_HEIGHT,
    SETTINGS_INPUT_HEIGHT, SETTINGS_BUTTON_HEIGHT, SETTINGS_BUTTON_WIDTH,
    SETTINGS_TITLE_BAR_HEIGHT, SETTINGS_CLOSE_BUTTON_SIZE, SETTINGS_SHADOW_BLUR_RADIUS,
    SETTINGS_CONTAINER_MARGIN, SETTINGS_CONTENT_MARGIN, SETTINGS_CONTENT_SPACING,
    SETTINGS_SHADOW_ALPHA,
    SETTINGS_DIALOG_TITLE, SETTINGS_CLOSE_BUTTON_TEXT, SETTINGS_SECTION_SAVE_LOCATION,
    SETTINGS_BROWSE_BUTTON_TEXT, SETTINGS_SECTION_QUALITY_FORMAT,
    SETTINGS_LABEL_VIDEO_QUALITY, SETTINGS_LABEL_AUDIO_QUALITY, SETTINGS_LABEL_FORMAT,
    SETTINGS_SECTION_GENERAL, SETTINGS_LABEL_MAX_DOWNLOADS, SETTINGS_SECTION_ADVANCED,
    SETTINGS_CHECKBOX_NORMALIZE, SETTINGS_CHECKBOX_ACCELERATION,
    SETTINGS_BUTTON_CANCEL, SETTINGS_BUTTON_SAVE, SETTINGS_FOLDER_DIALOG_TITLE,
    SETTINGS_ERROR_TITLE, SETTINGS_ERROR_NO_FOLDER, SETTINGS_ERROR_CANNOT_CREATE_FOLDER,
    SETTINGS_ERROR_INVALID_FOLDER,
    SETTINGS_FONT_FAMILY, SETTINGS_TITLE_FONT_SIZE, SETTINGS_SECTION_FONT_SIZE,
    FORMAT_MP3
)
from resources.styles import (
    SETTINGS_CONTAINER_STYLE, SETTINGS_TITLE_LABEL_STYLE, SETTINGS_CLOSE_BUTTON_STYLE,
    SETTINGS_SECTION_LABEL_STYLE, SETTINGS_LABEL_STYLE, SETTINGS_BROWSE_BUTTON_STYLE,
    SETTINGS_INPUT_STYLE, SETTINGS_COMBO_STYLE, SETTINGS_CHECKBOX_STYLE,
    SETTINGS_CANCEL_BUTTON_STYLE, SETTINGS_SAVE_BUTTON_STYLE
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

class SettingsDialog(QDialog):
    """다운로드 설정 다이얼로그"""
    
    def __init__(self, current_settings, parent=None):
        super().__init__(parent)
        
        # Frameless Window 설정
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        self.resize(SETTINGS_DIALOG_WIDTH, SETTINGS_DIALOG_HEIGHT)
        self.settings = current_settings
        self.oldPos = None
        
        self._setup_ui()
        self._on_format_changed(self.settings[KEY_FORMAT])  # 초기 상태 반영
        
    def _setup_ui(self):
        """UI 설정 - 메인 구조 생성"""
        # 메인 레이아웃 (투명 배경 위)
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(
            SETTINGS_CONTAINER_MARGIN, SETTINGS_CONTAINER_MARGIN,
            SETTINGS_CONTAINER_MARGIN, SETTINGS_CONTAINER_MARGIN
        )
        
        # 실제 컨텐츠가 담길 컨테이너 (흰색 배경, 둥근 모서리)
        container = self._create_container()
        main_layout.addWidget(container)
        
        # 컨테이너 내부 레이아웃
        layout = QVBoxLayout(container)
        layout.setContentsMargins(*SETTINGS_CONTENT_MARGIN)
        layout.setSpacing(SETTINGS_CONTENT_SPACING)
        
        # 1. 커스텀 타이틀 바
        self._create_title_bar(layout)
        
        # 2. 폼 영역
        form_layout = QVBoxLayout()
        form_layout.setSpacing(SETTINGS_CONTENT_SPACING)
        
        self._create_folder_section(form_layout)
        self._create_quality_section(form_layout)
        self._create_general_section(form_layout)
        self._create_advanced_section(form_layout)
        
        layout.addLayout(form_layout)
        layout.addStretch()
        
        # 3. 하단 버튼 (저장/취소)
        self._create_button_section(layout)

    def _create_container(self):
        """컨테이너 프레임 생성"""
        container = QFrame()
        container.setObjectName("Container")
        container.setStyleSheet(SETTINGS_CONTAINER_STYLE)
        
        # 그림자 효과
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(SETTINGS_SHADOW_BLUR_RADIUS)
        shadow.setXOffset(0)
        shadow.setYOffset(0)
        shadow.setColor(QColor(0, 0, 0, SETTINGS_SHADOW_ALPHA))
        container.setGraphicsEffect(shadow)
        
        return container

    def _create_title_bar(self, layout):
        """타이틀 바 생성"""
        title_frame = QFrame()
        title_frame.setFixedHeight(SETTINGS_TITLE_BAR_HEIGHT)
        title_frame.setStyleSheet("background: transparent;")
        
        title_layout = QHBoxLayout(title_frame)
        title_layout.setContentsMargins(0, 0, 0, 0)
        
        title_lbl = QLabel(SETTINGS_DIALOG_TITLE)
        title_lbl.setFont(QFont(SETTINGS_FONT_FAMILY, SETTINGS_TITLE_FONT_SIZE, QFont.Bold))
        title_lbl.setStyleSheet(SETTINGS_TITLE_LABEL_STYLE)
        
        close_btn = QPushButton(SETTINGS_CLOSE_BUTTON_TEXT)
        close_btn.setFixedSize(SETTINGS_CLOSE_BUTTON_SIZE, SETTINGS_CLOSE_BUTTON_SIZE)
        close_btn.setCursor(Qt.PointingHandCursor)
        close_btn.clicked.connect(self.reject)
        close_btn.setStyleSheet(SETTINGS_CLOSE_BUTTON_STYLE)
        
        title_layout.addWidget(title_lbl)
        title_layout.addStretch()
        title_layout.addWidget(close_btn)
        
        layout.addWidget(title_frame)

    def _create_folder_section(self, layout):
        """저장 위치 섹션 생성"""
        self._create_section_label(SETTINGS_SECTION_SAVE_LOCATION, layout)
        
        folder_layout = QHBoxLayout()
        folder_layout.setSpacing(10)
        
        self.folder_line = QLineEdit(self.settings[KEY_DOWNLOAD_FOLDER])
        self.folder_line.setReadOnly(True)
        self.folder_line.setFixedHeight(SETTINGS_INPUT_HEIGHT)
        self.folder_line.setStyleSheet(SETTINGS_INPUT_STYLE)
        
        self.browse_btn = QPushButton(SETTINGS_BROWSE_BUTTON_TEXT)
        self.browse_btn.setCursor(Qt.PointingHandCursor)
        self.browse_btn.setFixedHeight(SETTINGS_INPUT_HEIGHT)
        self.browse_btn.clicked.connect(self._browse_folder)
        self.browse_btn.setStyleSheet(SETTINGS_BROWSE_BUTTON_STYLE)
        
        folder_layout.addWidget(self.folder_line)
        folder_layout.addWidget(self.browse_btn)
        layout.addLayout(folder_layout)

    def _create_quality_section(self, layout):
        """품질 및 포맷 섹션 생성"""
        self._create_section_label(SETTINGS_SECTION_QUALITY_FORMAT, layout)
        
        grid_layout = QFormLayout()
        grid_layout.setSpacing(10)
        grid_layout.setLabelAlignment(Qt.AlignLeft)
        
        # 화질
        self.quality_combo = self._create_combo(
            VIDEO_QUALITY_OPTIONS, 
            self.settings[KEY_VIDEO_QUALITY]
        )
        grid_layout.addRow(self._create_label(SETTINGS_LABEL_VIDEO_QUALITY), self.quality_combo)
        
        # 음질
        self.audio_quality_combo = self._create_combo(
            AUDIO_QUALITY_OPTIONS,
            self.settings[KEY_AUDIO_QUALITY]
        )
        grid_layout.addRow(self._create_label(SETTINGS_LABEL_AUDIO_QUALITY), self.audio_quality_combo)
        
        # 포맷
        self.format_combo = self._create_combo(
            FORMAT_OPTIONS,
            self.settings[KEY_FORMAT]
        )
        self.format_combo.currentTextChanged.connect(self._on_format_changed)
        grid_layout.addRow(self._create_label(SETTINGS_LABEL_FORMAT), self.format_combo)
        
        layout.addLayout(grid_layout)

    def _create_general_section(self, layout):
        """일반 설정 섹션 생성"""
        self._create_section_label(SETTINGS_SECTION_GENERAL, layout)
        
        general_grid = QFormLayout()
        general_grid.setSpacing(10)
        general_grid.setLabelAlignment(Qt.AlignLeft)
        
        # 언어 선택
        from locales import SUPPORTED_LANGUAGES
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
        general_grid.addRow(self._create_label("언어 / Language:"), self.language_combo)
        
        # 최대 동시 다운로드 수
        self.max_downloads_spin = QSpinBox()
        self.max_downloads_spin.setRange(*MAX_DOWNLOADS_RANGE)
        self.max_downloads_spin.setValue(
            int(self.settings.get(KEY_MAX_DOWNLOADS, DEFAULT_MAX_DOWNLOADS))
        )
        self.max_downloads_spin.setFixedHeight(SETTINGS_INPUT_HEIGHT)
        self.max_downloads_spin.setStyleSheet(SETTINGS_INPUT_STYLE)
        general_grid.addRow(self._create_label(SETTINGS_LABEL_MAX_DOWNLOADS), self.max_downloads_spin)
        
        layout.addLayout(general_grid)

    def _create_advanced_section(self, layout):
        """고급 기능 섹션 생성"""
        self._create_section_label(SETTINGS_SECTION_ADVANCED, layout)
        
        # 음량 평준화 체크박스
        self.norm_check = QCheckBox(SETTINGS_CHECKBOX_NORMALIZE)
        self.norm_check.setToolTip(
            "모든 영상의 소리 크기를 방송 표준(-14 LUFS)으로 통일합니다.\n"
            "변환 시간이 조금 더 걸립니다."
        )
        self.norm_check.setChecked(self.settings.get(KEY_NORMALIZE_AUDIO, DEFAULT_NORMALIZE))
        self.norm_check.setStyleSheet(SETTINGS_CHECKBOX_STYLE)
        layout.addWidget(self.norm_check)
        
        # 다운로드 가속 체크박스
        self.accel_check = QCheckBox(SETTINGS_CHECKBOX_ACCELERATION)
        self.accel_check.setToolTip(
            "파일을 여러 조각으로 나누어 동시에 받습니다.\n"
            "다운로드 속도가 향상됩니다.\n"
            "(선택 시 최대 다운로드 수는 1로 고정됩니다)"
        )
        self.accel_check.setChecked(self.settings.get(KEY_USE_ACCELERATION, DEFAULT_ACCELERATION))
        self.accel_check.stateChanged.connect(lambda state: self._on_acceleration_changed(state == 2))
        self.accel_check.setStyleSheet(SETTINGS_CHECKBOX_STYLE)
        layout.addWidget(self.accel_check)
        
        # 초기 상태 반영 (다운로드 가속이 체크되어 있으면 최대 다운로드 수 비활성화)
        self._on_acceleration_changed(self.accel_check.isChecked())
        
        # 쿠키 연동 섹션은 기능 미사용으로 제거됨

    def _create_button_section(self, layout):
        """하단 버튼 섹션 생성"""
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)
        btn_layout.addStretch()
        
        cancel_btn = QPushButton(SETTINGS_BUTTON_CANCEL)
        cancel_btn.setFixedSize(SETTINGS_BUTTON_WIDTH, SETTINGS_BUTTON_HEIGHT)
        cancel_btn.setCursor(Qt.PointingHandCursor)
        cancel_btn.clicked.connect(self.reject)
        cancel_btn.setStyleSheet(SETTINGS_CANCEL_BUTTON_STYLE)
        
        save_btn = QPushButton(SETTINGS_BUTTON_SAVE)
        save_btn.setFixedSize(SETTINGS_BUTTON_WIDTH, SETTINGS_BUTTON_HEIGHT)
        save_btn.setCursor(Qt.PointingHandCursor)
        save_btn.clicked.connect(self.accept)
        save_btn.setStyleSheet(SETTINGS_SAVE_BUTTON_STYLE)
        
        btn_layout.addWidget(cancel_btn)
        btn_layout.addWidget(save_btn)
        
        layout.addLayout(btn_layout)

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
    
    def mousePressEvent(self, event):
        """윈도우 드래그 - 마우스 누름"""
        if event.button() == Qt.LeftButton:
            self.oldPos = event.globalPos()

    def mouseMoveEvent(self, event):
        """윈도우 드래그 - 마우스 이동"""
        if self.oldPos is not None and event.buttons() == Qt.LeftButton:
            delta = QPoint(event.globalPos() - self.oldPos)
            self.move(self.x() + delta.x(), self.y() + delta.y())
            self.oldPos = event.globalPos()

    def mouseReleaseEvent(self, event):
        """윈도우 드래그 - 마우스 놓음"""
        if event.button() == Qt.LeftButton:
            self.oldPos = None

    def _browse_folder(self):
        """폴더 선택 다이얼로그"""
        folder = QFileDialog.getExistingDirectory(
            self, SETTINGS_FOLDER_DIALOG_TITLE, self.folder_line.text()
        )
        if folder:
            self.folder_line.setText(folder)
            
    def _on_format_changed(self, format_type):
        """포맷 변경 시 화질/음질 콤보박스 활성화 상태 업데이트"""
        is_audio_only = (format_type == FORMAT_MP3)
        self.quality_combo.setEnabled(not is_audio_only)
        self.audio_quality_combo.setEnabled(True)
    
    def _on_acceleration_changed(self, checked):
        """다운로드 가속 체크박스 상태 변경 시 호출"""
        if checked:
            # 다운로드 가속이 켜지면 최대 다운로드 수를 1로 고정하고 비활성화
            self.max_downloads_spin.setValue(1)
            self.max_downloads_spin.setEnabled(False)
        else:
            # 다운로드 가속이 꺼지면 최대 다운로드 수 편집 가능
            self.max_downloads_spin.setEnabled(True)

    # ===== 다이얼로그 결과 처리 =====
    
    def accept(self):
        """저장 버튼 클릭 시 설정 저장"""
        folder_path = self.folder_line.text().strip()
        
        # 폴더 경로 유효성 검사
        if not folder_path:
            QMessageBox.warning(self, SETTINGS_ERROR_TITLE, SETTINGS_ERROR_NO_FOLDER)
            return
        
        # 폴더가 없으면 생성 시도
        if not os.path.exists(folder_path):
            try:
                os.makedirs(folder_path, exist_ok=True)
            except Exception as e:
                QMessageBox.warning(self, SETTINGS_ERROR_TITLE, 
                                  SETTINGS_ERROR_CANNOT_CREATE_FOLDER.format(error=str(e)))
                return
        
        # 폴더가 디렉토리가 아닌 경우
        if not os.path.isdir(folder_path):
            QMessageBox.warning(self, SETTINGS_ERROR_TITLE, SETTINGS_ERROR_INVALID_FOLDER)
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
