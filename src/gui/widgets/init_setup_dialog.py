from PyQt5.QtWidgets import (QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QComboBox)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QColor

from gui.widgets.base_dialog import BaseDialog

from locales import SUPPORTED_LANGUAGES, DEFAULT_LANGUAGE, set_language
from locales.strings import STR
from constants import BTN_TEXT_CLOSE_X, KEY_LANGUAGE
from gui.windows.settings_dialog import save_settings, load_settings
from resources.styles import (
    SETTINGS_SAVE_BUTTON_STYLE,
    SETTINGS_FONT_FAMILY, 
    MESSAGE_BTN_HEIGHT,
    MESSAGE_BODY_STYLE,
    SETTINGS_COMBO_STYLE
)

class InitSetupDialog(BaseDialog):
    """
    초기 설정 대화상자 (첫 실행 시)
    - 언어 선택 기능 제공
    - 필수 구성요소 다운로드 안내
    """
    
    def __init__(self, parent=None):
        super().__init__(
            parent=parent, 
            title=STR.TITLE_INIT_SETUP, 
            icon_text="👋", 
            show_close_btn=True, 
            show_divider=True
        )
        
        self.settings = load_settings()
        self.current_lang = DEFAULT_LANGUAGE # 항상 기본값으로 시작 (사용자 요청)
        
        self._setup_content()
        self._setup_buttons()
        self._update_text() # 초기 텍스트 설정
        
    def _setup_content(self):
        # Language Selection Section
        lang_layout = QHBoxLayout()
        self.lang_label = QLabel()
        self.lang_label.setFont(QFont(SETTINGS_FONT_FAMILY, 10, QFont.Bold))
        lang_layout.addWidget(self.lang_label)
        
        self.lang_combo = QComboBox()
        self.lang_combo.setStyleSheet(SETTINGS_COMBO_STYLE)
        self.lang_combo.setMinimumWidth(150)
        self.lang_combo.setCursor(Qt.PointingHandCursor)
        
        # 언어 목록 추가
        for code, name in SUPPORTED_LANGUAGES.items():
            self.lang_combo.addItem(name, code)
            
        # 현재 언어 선택
        index = self.lang_combo.findData(self.current_lang)
        if index >= 0:
            self.lang_combo.setCurrentIndex(index)
            
        self.lang_combo.currentIndexChanged.connect(self._on_language_changed)
        lang_layout.addWidget(self.lang_combo)
        lang_layout.addStretch()
        
        self.content_layout.addLayout(lang_layout)
        
        # Message Body
        self.msg_label = QLabel()
        self.msg_label.setFont(QFont(SETTINGS_FONT_FAMILY, 10))
        self.msg_label.setStyleSheet(MESSAGE_BODY_STYLE)
        self.msg_label.setWordWrap(True)
        self.msg_label.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        self.msg_label.setMinimumWidth(400)
        self.content_layout.addWidget(self.msg_label)

    def _setup_buttons(self):
        self.start_btn = QPushButton()
        self.start_btn.setFixedWidth(120)
        self.start_btn.setFixedHeight(MESSAGE_BTN_HEIGHT)
        self.start_btn.setCursor(Qt.PointingHandCursor)
        self.start_btn.clicked.connect(self._on_start_clicked)
        self.start_btn.setStyleSheet(SETTINGS_SAVE_BUTTON_STYLE) 
        self.button_layout.addWidget(self.start_btn)

    def _update_text(self):
        """현재 언어 설정에 맞춰 UI 텍스트 업데이트"""
        self.title_label.setText(STR.TITLE_INIT_SETUP)
        self.lang_label.setText(STR.LABEL_LANGUAGE_SELECT)
        self.msg_label.setText(STR.MSG_CONFIRM_INIT_DOWNLOAD)
        self.start_btn.setText(STR.BTN_START_SETUP)

    def _on_language_changed(self, index):
        """언어 변경 시 즉시 반영"""
        lang_code = self.lang_combo.itemData(index)
        if lang_code != self.current_lang:
            self.current_lang = lang_code
            set_language(self.current_lang) # 전역 STR 업데이트
            self._update_text() # UI 텍스트 갱신

    def _on_start_clicked(self):
        """설정 저장 및 진행"""
        # 언어 설정 저장
        self.settings[KEY_LANGUAGE] = self.current_lang
        save_settings(self.settings)
        self.accept()
