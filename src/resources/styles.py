"""Application stylesheet constants."""

# Color constants.
COLOR_WAITING = "#D1D3D4"    # Waiting for download or metadata loading.
COLOR_DOWNLOADING = "#DBC4F0" # Downloading.
COLOR_FINISHED = "#B8E8FC"    # Finished.
COLOR_ERROR = "#FF0000"       # Failed.
COLOR_PAUSED = "#FFE0B2"      # Paused state, apricot.
COLOR_PRIMARY = "#5F428B"     # Main purple.
COLOR_DEEP_ORANGE = "#E65100" # Deep orange for stopped-state icons and borders.

# Text colors.
COLOR_TEXT_PRIMARY = "#333333"
COLOR_TEXT_SECONDARY = "#444444"
COLOR_TEXT_GRAY = "#888888"
COLOR_TEXT_LIGHT_GRAY = "#999999"
COLOR_DIVIDER = "#E0E0E0"

# ==========================================
# Shared UI constants are managed here.
# ==========================================

# Font settings.
SETTINGS_FONT_FAMILY = "Segoe UI"
SETTINGS_TITLE_FONT_SIZE = 12
SETTINGS_SECTION_FONT_SIZE = 10

# Dialog sizes and layout.
SETTINGS_DIALOG_WIDTH = 800
SETTINGS_DIALOG_HEIGHT = 600
SETTINGS_CONTAINER_MARGIN = 0
SETTINGS_CONTENT_MARGIN = (15, 15, 15, 15)
SETTINGS_CONTENT_SPACING = 10

# UI element sizes.
SETTINGS_INPUT_HEIGHT = 30
SETTINGS_BUTTON_HEIGHT = 36
TEXT_BUTTON_WIDTH_PADDING = 30
DOWNLOAD_BUTTON_WIDTH_PADDING = TEXT_BUTTON_WIDTH_PADDING
SETTINGS_BUTTON_WIDTH_PADDING = TEXT_BUTTON_WIDTH_PADDING
SETTINGS_DIALOG_TITLE_ICON_SIZE = 24
SETTINGS_DIALOG_TITLE_BUTTON_SIZE = 24
SETTINGS_DIALOG_TITLE_BUTTON_ICON_SIZE = 18

# Shadow effects.
SETTINGS_SHADOW_BLUR_RADIUS = 15
SETTINGS_SHADOW_ALPHA = 30

# Download dialog size.
DOWNLOAD_DIALOG_WIDTH = 450
DOWNLOAD_DIALOG_HEIGHT = 250

# Message dialog button size.
MESSAGE_BTN_HEIGHT = 32

# Startup dialog style.
STARTUP_DIALOG_WIDTH = 450
STARTUP_DIALOG_HEIGHT = 200
STARTUP_LABEL_STYLE = "color: #555555; font-size: 11pt;"
STARTUP_PROGRESS_STYLE = """
QProgressBar {
    border: none;
    background: #EAEAEA;
    border-radius: 3px;
    height: 6px;
}
QProgressBar::chunk {
    background-color: #5F428B;
    border-radius: 3px;
}
"""

# Main window style.
MAIN_WINDOW_STYLE = """
QMainWindow {
    background-color: transparent;
}
QWidget {
    color: #333333;
    font-family: 'Segoe UI', 'Malgun Gothic', sans-serif;
}
/* QScrollArea 스타일링 */
QScrollArea {
    background: transparent;
    border: none;
}
/* 스크롤바 스타일링 */
QScrollBar:vertical {
    background: transparent;
    width: 6px;
    margin: 0px;
}
QScrollBar::handle:vertical {
    background: #D1D1D1;
    border-radius: 3px;
    min-height: 30px;
}
QScrollBar::handle:vertical:hover { 
    background: #A8A8A8; 
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { 
    height: 0px; 
}
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical { 
    background: none; 
}
"""

# ==========================================
# Main-window UI settings moved from constants.py.
# ==========================================

# Main-window size and position.
MAIN_WINDOW_X = 100
MAIN_WINDOW_Y = 100
MAIN_WINDOW_WIDTH = 1200
MAIN_WINDOW_HEIGHT = 800

# Main-window title and app info.
APP_TITLE_COLOR = "#5F428B"

# Main-window layout.
MAIN_LAYOUT_MARGINS = (5, 5, 5, 5)
MAIN_LAYOUT_SPACING = 5
WINDOW_RESIZE_CONTENT_MARGIN = 5

# Title bar.
TITLE_BAR_HEIGHT = 30
TITLE_BAR_MARGINS = (10, 0, 10, 0)
TITLE_BAR_SPACING = 10
TITLE_BAR_FONT_FAMILY = "Segoe UI"
TITLE_BAR_FONT_SIZE = 11
TITLE_BAR_BUTTON_SIZE = 30
TITLE_BAR_BUTTON_ICON_SIZE = 24

# URL input section.
URL_INPUT_SECTION_HEIGHT = 70
URL_INPUT_CONTAINER_MARGINS = (10, 8, 10, 8)
URL_INPUT_CONTAINER_SPACING = 10
URL_INPUT_HEIGHT = 40
URL_INPUT_FONT_FAMILY = "Segoe UI"
URL_INPUT_FONT_SIZE = 11
TOGGLE_BUTTON_SIZE = 50
SETTINGS_BUTTON_SIZE = 40

# Download button.
DOWNLOAD_BUTTON_HEIGHT = 40
DOWNLOAD_BUTTON_FONT_FAMILY = "Segoe UI"
DOWNLOAD_BUTTON_FONT_SIZE = 10

# Task list section.
TASK_LIST_MARGINS = (10, 0, 10, 0)
TASK_LIST_SPACING = 10
TASK_LIST_MIN_HEIGHT = 360
EMPTY_STATE_FONT_FAMILY = "Segoe UI"
EMPTY_STATE_FONT_SIZE = 11

# Status bar.
STATUS_BAR_HEIGHT = 35
STATUS_BAR_MARGINS = (10, 0, 10, 0)
STATUS_BAR_SPACING = 10
STATUS_BAR_FONT_FAMILY = "Segoe UI"
STATUS_BAR_FONT_SIZE = 9
STATUS_CONTROL_HEIGHT = 32
STATUS_SORT_BUTTON_MIN_WIDTH = 80
STATUS_SORT_BUTTON_HORIZONTAL_PADDING = 40
STATUS_SORT_BUTTON_ICON_SIZE = 18
STATUS_COUNTER_HORIZONTAL_PADDING = 10
PROGRESS_SLIDER_MIN = 0
PROGRESS_SLIDER_MAX = 100
PROGRESS_SLIDER_DEFAULT = 0

# Task card UI size constants.
CARD_HEIGHT = 130
THUMBNAIL_WIDTH = 160
THUMBNAIL_HEIGHT = 90
BUTTON_SIZE = 40

# Button color constants.
COLOR_BTN_RED = "#F44336"
COLOR_BTN_GREEN = "#4CAF50"
COLOR_BTN_BLUE = "#2196F3"
COLOR_BTN_ORANGE = "#FF9800"
COLOR_BTN_GRAY = "#999999"

# ==========================================
# Bottom-up minimum-size constants for individual parts.
# Do not force a hard minimum on the whole window.
# Instead, set each part minimum width and height
# so the layout system naturally determines the window minimum size.
# ==========================================
MIN_URL_INPUT_WIDTH = 200
MIN_DOWNLOAD_BUTTON_WIDTH = 80
MIN_TITLE_LABEL_WIDTH = 100
MIN_STATUS_LABEL_WIDTH = 100
MIN_SETTINGS_TAB_WIDTH = 300

# Central widget style.
CENTRAL_WIDGET_STYLE = """
QWidget#CentralWidget {
    background-color: #FFFFFF;
    border-radius: 0px;
}
"""

# Central widget style for maximized state.
CENTRAL_WIDGET_MAXIMIZED_STYLE = """
QWidget#CentralWidget {
    background-color: #FFFFFF;
    border: none;
    border-radius: 0px;
}
"""

# Title-bar style.
TITLE_BAR_STYLE = "background: transparent; border: none;"

# Minimize button style.
MINIMIZE_BUTTON_STYLE = """
QPushButton {
    background-color: transparent;
    color: #999999;
    border-radius: 14px;
    font-weight: bold;
}
QPushButton:hover {
    background-color: #E8F4FD;
    color: #2196F3;
}
"""

# Close button style.
CLOSE_BUTTON_STYLE = """
QPushButton {
    background-color: transparent;
    color: #999999;
    border-radius: 14px;
    font-weight: bold;
}
QPushButton:hover {
    background-color: #FFEEEE;
    color: #FF5252;
}
"""

# Maximize/restore button style.
MAXIMIZE_BUTTON_STYLE = """
QPushButton {
    background-color: transparent;
    color: #999999;
    border-radius: 14px;
    font-weight: bold;
}
QPushButton:hover {
    background-color: #E8FDE8;
    color: #4CAF50;
}
"""

# URL input section style.
URL_INPUT_CONTAINER_STYLE = """
QFrame {
    background-color: #F8F9FA;
    border-radius: 10px;
}
"""

URL_INPUT_STYLE = """
QLineEdit {
    border: 1px solid #E0E0E0;
    border-radius: 8px;
    padding: 0 12px;
    background-color: #FFFFFF;
    color: #333333;
}
QLineEdit:focus {
    border: 1px solid #5F428B;
    background-color: #FFFFFF;
}
"""

# Download button style.
DOWNLOAD_BUTTON_STYLE = """
QPushButton {
    background-color: #5F428B;
    color: #FFFFFF;
    border: none;
    border-top-left-radius: 8px;
    border-bottom-left-radius: 8px;
}
QPushButton:hover { background-color: #70529E; }
QPushButton:pressed { background-color: #4E3672; }
QPushButton:disabled { background-color: #E0E0E0; color: #A0A0A0; }
"""

# Settings button style.
SETTINGS_BUTTON_STYLE = """
QPushButton {
    background-color: #EDEDED;
    color: #555555;
    border: none;
    border-top-right-radius: 8px;
    border-bottom-right-radius: 8px;
}
QPushButton:hover { background-color: #DCDCDC; }
QPushButton:pressed { background-color: #CFCFCF; }
"""

# Status-bar style.
STATUS_BAR_STYLE = "background: transparent;"

STATUS_LABEL_STYLE = "color: #666666;"

STATUS_COUNTER_STYLE = "color: #666666;"

STATUS_SORT_BUTTON_STYLE = """
QToolButton {
    border: 1px solid #E0E0E0;
    border-radius: 7px;
    padding: 0 5px;
    background-color: #F5F5F5;
    color: #555555;
    font-family: 'Segoe UI';
    font-size: 9pt;
}
QToolButton:hover {
    background-color: #E8E8E8;
    border-color: #D6D6D6;
}
QToolButton:pressed {
    background-color: #DDDDDD;
    border-color: #CFCFCF;
}
QToolButton::menu-indicator {
    image: none;
    width: 0px;
}
"""

STATUS_SORT_MENU_STYLE = """
QMenu {
    background-color: #FFFFFF;
    border: 1px solid #E0E0E0;
    border-radius: 6px;
    padding: 4px;
    color: #444444;
    font-family: 'Segoe UI';
    font-size: 9pt;
}
QMenu::item {
    padding: 6px 28px 6px 12px;
    border-radius: 4px;
}
QMenu::item:selected {
    background-color: #F3F3F3;
}
QMenu::indicator {
    width: 14px;
    height: 14px;
}
"""

# Progress slider style.
PROGRESS_SLIDER_STYLE = """
QSlider::groove:horizontal {
    border: none;
    background: #E0E0E0;
    height: 4px;
    border-radius: 2px;
}
QSlider::sub-page:horizontal {
    background: #BDBDBD;
    height: 4px;
    border-radius: 2px;
}
QSlider::handle:horizontal {
    width: 0px; 
    height: 0px; 
    margin: 0; 
    background: transparent;
}
"""

# Selected-state color.
COLOR_SELECTED = COLOR_PRIMARY.lstrip('#')  # Selected using the main theme color.

# Task card style.
def get_card_style(color_hex, selected=False):
    """
    Build a card border style.
    
    Args:
        color_hex: Color code, such as #D1D3D4 or D1D3D4.
        selected: Whether the card is selected.
    """
    # Add a # prefix if it is missing.
    if not color_hex.startswith('#'):
        color_hex = '#' + color_hex
    
    # Define direct widget styles without selectors.
    if selected:
        # Selected state: changed background and emphasized border.
        return f"""
background-color: #F3E8FF;
border: 4px solid #{COLOR_SELECTED};
border-radius: 8px;
"""
    else:
        return f"""
background-color: #FFFFFF;
border: 4px solid {color_hex};
border-radius: 8px;
"""

# Thumbnail label style.
# Thumbnail label style.
THUMBNAIL_LABEL_STYLE = """
QLabel {
    background: #F0F0F0;
    border-radius: 4px;
    border: none;
    color: #888;
}
"""

# Title label style.
TITLE_LABEL_STYLE = """
QLabel {
    color: #333333;
    border: none;
    background: transparent;
    font-family: 'Segoe UI';
    font-size: 11pt;
    font-weight: bold;
}
"""

# Uploader label style.
UPLOADER_LABEL_STYLE = """
QLabel {
    color: #888888;
    border: none;
    background: transparent;
    font-family: 'Segoe UI';
    font-size: 9pt;
}
"""

# Progress bar style.
PROGRESS_BAR_STYLE = """
QProgressBar {
    border: none;
    background: #EAEAEA;
    border-radius: 3px;
}
QProgressBar::chunk {
    background-color: #5F428B;
    border-radius: 3px;
}
"""

# Progress bar style for finished state.
PROGRESS_BAR_FINISHED_STYLE = """
QProgressBar { border: none; background: #EAEAEA; border-radius: 3px; }
QProgressBar::chunk { background-color: #4CAF50; border-radius: 3px; }
"""

# Progress bar style for error state.
PROGRESS_BAR_ERROR_STYLE = """
QProgressBar { border: none; background: #EAEAEA; border-radius: 3px; }
QProgressBar::chunk { background-color: #F44336; border-radius: 3px; }
"""

# Percent label style.
# Percent label style.
PERCENT_LABEL_STYLE = """
QLabel {
    color: #5F428B;
    border: none;
    background: transparent;
    font-family: 'Segoe UI';
    font-size: 9pt;
    font-weight: bold;
}
"""

# Status label style, shared.
STATUS_LABEL_NORMAL_STYLE = """
QLabel {
    color: #666666;
    border: none;
    background: transparent;
    font-family: 'Segoe UI';
    font-size: 9pt;
}
"""

STATUS_LABEL_SUCCESS_STYLE = """
QLabel {
    color: #4CAF50;
    font-weight: bold;
    border: none;
    background: transparent;
    font-family: 'Segoe UI';
    font-size: 9pt;
}
"""

STATUS_LABEL_ERROR_STYLE = """
QLabel {
    color: #F44336;
    font-weight: bold;
    border: none;
    background: transparent;
    font-family: 'Segoe UI';
    font-size: 9pt;
}
"""

STATUS_LABEL_WARNING_STYLE = """
QLabel {
    color: #FF9800;
    font-weight: bold;
    border: none;
    background: transparent;
    font-family: 'Segoe UI';
    font-size: 9pt;
}
"""

# Size label style.
SIZE_LABEL_STYLE = """
QLabel {
    color: #999999;
    border: none;
    background: transparent;
    font-family: 'Segoe UI';
    font-size: 9pt;
}
"""

# Action button style.
ACTION_BUTTON_STYLE = """
QPushButton {
    background-color: #F5F5F5;
    border: 1px solid #E0E0E0;
    border-radius: 6px;
    padding: 0px;
    margin: 0px;
}
QPushButton:hover { background-color: #E0E0E0; }
QPushButton:pressed { background-color: #D0D0D0; }
"""

# Empty-state label style.
EMPTY_LABEL_STYLE = "color: #AAAAAA; padding: 20px;"

# ===== Settings Dialog Style =====

# Settings dialog container style.
SETTINGS_CONTAINER_STYLE = """
QFrame#Container {
    background-color: #FFFFFF;
    border: 1px solid #E0E0E0;
    border-radius: 15px;
}
QLabel {
    font-family: 'Segoe UI', sans-serif;
    color: #333333;
}
"""

# Settings dialog title label style.
SETTINGS_TITLE_LABEL_STYLE = "color: #333333;"

# Settings dialog close button style.
SETTINGS_CLOSE_BUTTON_STYLE = """
QPushButton {
    background: transparent;
    border: none;
    color: #999999;
    border-radius: 12px;
    font-weight: bold;
}
QPushButton:hover {
    background-color: #FFEEEE;
    color: #FF5252;
}
"""

# Settings dialog section label style.
SETTINGS_SECTION_LABEL_STYLE = "color: #5F428B; margin-top: 10px; margin-bottom: 5px;"

# Settings dialog regular label style.
SETTINGS_LABEL_STYLE = "color: #555555;"

# Settings dialog browse button style.
SETTINGS_BROWSE_BUTTON_STYLE = """
QPushButton {
    background-color: #F0F0F0;
    border: 1px solid #D0D0D0;
    border-radius: 6px;
    padding: 0 10px;
    color: #555555;
    font-family: 'Segoe UI';
}
QPushButton:hover { background-color: #E0E0E0; }
QPushButton:pressed { background-color: #D0D0D0; }
"""

# Settings dialog input field style.
SETTINGS_INPUT_STYLE = """
QLineEdit, QSpinBox {
    border: 1px solid #E0E0E0;
    border-radius: 6px;
    padding: 0 10px;
    background-color: #F9F9F9;
    color: #333333;
    font-family: 'Segoe UI';
}
QSpinBox::up-button, QSpinBox::down-button {
    width: 20px;
}
"""

# Settings dialog combo-box style.
SETTINGS_COMBO_STYLE = """
QComboBox {
    border: 1px solid #E0E0E0;
    border-radius: 6px;
    padding: 0 34px 0 10px;
    background-color: #FFFFFF;
    color: #333333;
    font-family: 'Segoe UI';
}
QComboBox::drop-down {
    border: none;
    border-left: 1px solid #E0E0E0;
    background-color: #F9F9F9;
    width: 32px;
}
QComboBox::down-arrow {
    image: none;
    width: 0px;
    height: 0px;
}
"""

# Settings dialog numeric stepper style
SETTINGS_STEPPER_STYLE = """
QWidget#SettingsStepper {
    background-color: #F9F9F9;
    border: 1px solid #E0E0E0;
    border-radius: 6px;
}
QPushButton#SettingsStepperButton {
    background-color: transparent;
    border: none;
    border-radius: 6px;
}
QPushButton#SettingsStepperButton:hover {
    background-color: #EEEEEE;
}
QPushButton#SettingsStepperButton:pressed {
    background-color: #E0E0E0;
}
QPushButton#SettingsStepperButton:disabled {
    background-color: transparent;
}
QLineEdit#SettingsStepperValue {
    color: #333333;
    font-family: 'Segoe UI';
    font-weight: bold;
    border: none;
    border-left: 1px solid #E0E0E0;
    border-right: 1px solid #E0E0E0;
    background-color: #FFFFFF;
    padding: 0;
}
QLineEdit#SettingsStepperValue:focus {
    border-left: 1px solid #D0D0D0;
    border-right: 1px solid #D0D0D0;
    background-color: #FFFFFF;
}
"""

# Settings dialog checkbox style
SETTINGS_CHECKBOX_STYLE = """
QCheckBox {
    font-family: 'Segoe UI';
    font-size: 10pt;
    color: #333333;
    spacing: 5px;
}
QCheckBox::indicator {
    width: 18px;
    height: 18px;
}
"""

# Settings dialog cancel button style.
SETTINGS_CANCEL_BUTTON_STYLE = """
QPushButton {
    background-color: #F5F5F5;
    color: #666666;
    border: none;
    border-radius: 8px;
    font-weight: bold;
    font-family: 'Segoe UI';
    padding: 0 8px;
}
QPushButton:hover { background-color: #EEEEEE; }
"""

# Settings dialog save button style.
SETTINGS_SAVE_BUTTON_STYLE = """
QPushButton {
    background-color: #5F428B;
    color: #FFFFFF;
    border: none;
    border-radius: 8px;
    font-weight: bold;
    font-family: 'Segoe UI';
    padding: 0 8px;
}
QPushButton:hover { background-color: #70529E; }
QPushButton:pressed { background-color: #4E3672; }
"""

# Settings dialog tab style.
SETTINGS_TAB_STYLE = """
QTabWidget::pane {
    border: 1px solid #E0E0E0;
    border-radius: 5px;
    background: white;
}
QTabBar::tab {
    background: #F5F5F5;
    color: #666;
    padding: 6px 10px;
    border: 1px solid #E0E0E0;
    border-bottom: none;
    border-top-left-radius: 4px;
    border-top-right-radius: 4px;
    margin-right: 2px;
}
QTabBar::tab:selected {
    background: white;
    color: #5F428B;
    border-bottom: 1px solid white;
}
QTabBar::tab:hover:!selected {
    background: #EEEEEE;
}
"""

# Settings dialog update/delete button style.
SETTINGS_UPDATE_BUTTON_STYLE = """
QPushButton {
    background-color: #f0f0f0;
    border: 1px solid #ccc;
    border-radius: 5px;
    color: #333;
    padding: 10px;
}
QPushButton:hover {
    background-color: #e0e0e0;
}
"""

SETTINGS_UNINSTALL_BUTTON_STYLE = """
QPushButton {
    background-color: #ffebee;
    border: 1px solid #ffcdd2;
    border-radius: 5px;
    color: #d32f2f;
    padding: 10px;
}
QPushButton:hover {
    background-color: #ffcdd2;
}
"""

# Download progress dialog style.
DETAIL_LABEL_STYLE = f"color: {COLOR_TEXT_GRAY};"
INFO_LABEL_STYLE = f"color: {COLOR_TEXT_LIGHT_GRAY};"

# Message dialog style.
MESSAGE_TITLE_STYLE = f"color: {COLOR_TEXT_PRIMARY};"
MESSAGE_BODY_STYLE = f"color: {COLOR_TEXT_SECONDARY};"
MESSAGE_DIVIDER_STYLE = f"background-color: {COLOR_DIVIDER};"
