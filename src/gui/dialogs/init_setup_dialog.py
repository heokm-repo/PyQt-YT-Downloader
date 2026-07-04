from PyQt5.QtWidgets import (QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QComboBox)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QColor

from gui.dialogs.base_dialog import BaseDialog
from gui.widgets.button_sizing import set_text_button_minimum_width

from locales import SUPPORTED_LANGUAGES, DEFAULT_LANGUAGE, set_language
from locales.strings import STR
from constants import BTN_TEXT_CLOSE_X, KEY_LANGUAGE
from utils.settings_store import save_settings, load_settings
from resources.styles import (
    SETTINGS_SAVE_BUTTON_STYLE,
    SETTINGS_FONT_FAMILY, 
    MESSAGE_BTN_HEIGHT,
    MESSAGE_BODY_STYLE,
    SETTINGS_COMBO_STYLE
)

class InitSetupDialog(BaseDialog):
    """Initial setup dialog shown on first launch, with language selection and required-component download guidance."""
    
    def __init__(self, parent=None):
        super().__init__(
            parent=parent, 
            title=STR.TITLE_INIT_SETUP, 
            icon_text="mdi.hand-wave", 
            show_close_btn=True, 
            show_divider=True
        )
        
        self.settings = load_settings()
        self.current_lang = DEFAULT_LANGUAGE # Always start from the default language.
        
        self._setup_content()
        self._setup_buttons()
        self._update_text() # Set initial text.
        
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
        
        # Add language options.
        for code, name in SUPPORTED_LANGUAGES.items():
            self.lang_combo.addItem(name, code)
            
        # Select the current language.
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
        self.start_btn.setFixedHeight(MESSAGE_BTN_HEIGHT)
        self.start_btn.setCursor(Qt.PointingHandCursor)
        self.start_btn.clicked.connect(self._on_start_clicked)
        self.start_btn.setStyleSheet(SETTINGS_SAVE_BUTTON_STYLE) 
        self.button_layout.addWidget(self.start_btn)

    def _update_text(self):
        """Refresh UI text for the current language."""
        self.title_label.setText(STR.TITLE_INIT_SETUP)
        self.lang_label.setText(STR.LABEL_LANGUAGE_SELECT)
        self.msg_label.setText(STR.MSG_CONFIRM_INIT_DOWNLOAD)
        self.start_btn.setText(STR.BTN_START_SETUP)
        set_text_button_minimum_width(self.start_btn)

    def _on_language_changed(self, index):
        """Apply language changes immediately."""
        lang_code = self.lang_combo.itemData(index)
        if lang_code != self.current_lang:
            self.current_lang = lang_code
            set_language(self.current_lang) # Refresh the global STR object.
            self._update_text() # Refresh UI text.

    def _on_start_clicked(self):
        """Save settings and continue."""
        # Save the language setting.
        self.settings[KEY_LANGUAGE] = self.current_lang
        save_settings(self.settings)
        self.accept()
