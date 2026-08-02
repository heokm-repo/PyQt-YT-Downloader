"""Application stylesheet constants."""

from string import Template

from resources import colors as _colors


class _ThemedStyle(str):
    """Rendered QSS that retains its semantic-token template for rebuilding."""

    def __new__(cls, template: str):
        rendered = Template(template).substitute(vars(_colors))
        instance = super().__new__(cls, rendered)
        instance.template = template
        return instance


def _style(template: str) -> str:
    """Resolve semantic color tokens in a QSS template."""
    return _ThemedStyle(template)


def apply_theme(theme_name: str | None) -> str:
    """Activate a palette and rebuild every themed stylesheet constant."""
    active_theme = _colors.activate_theme(theme_name)
    for name, value in tuple(globals().items()):
        if isinstance(value, _ThemedStyle):
            globals()[name] = _ThemedStyle(value.template)
    return active_theme

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
STARTUP_LABEL_STYLE = _style("color: $COLOR_TEXT_DEFAULT; font-size: 11pt;")
STARTUP_PROGRESS_STYLE = _style("""
QProgressBar {
    border: none;
    background: $COLOR_PROGRESS_TRACK;
    border-radius: 3px;
    height: 6px;
}
QProgressBar::chunk {
    background-color: $COLOR_ACCENT;
    border-radius: 3px;
}
""")

# Main window style.
MAIN_WINDOW_STYLE = _style("""
QMainWindow {
    background-color: $COLOR_TRANSPARENT;
}
QWidget {
    color: $COLOR_TEXT_PRIMARY;
    font-family: 'Segoe UI', 'Malgun Gothic', sans-serif;
}
/* QScrollArea 스타일링 */
QScrollArea {
    background: $COLOR_TRANSPARENT;
    border: none;
}
/* 스크롤바 스타일링 */
QScrollBar:vertical {
    background: $COLOR_TRANSPARENT;
    width: 6px;
    margin: 0px;
}
QScrollBar::handle:vertical {
    background: $COLOR_SCROLLBAR_THUMB;
    border-radius: 3px;
    min-height: 30px;
}
QScrollBar::handle:vertical:hover {
    background: $COLOR_SCROLLBAR_THUMB_HOVER;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { 
    height: 0px; 
}
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical { 
    background: none; 
}
""")

# ==========================================
# Main-window UI settings moved from constants.py.
# ==========================================

# Main-window size and position.
MAIN_WINDOW_X = 100
MAIN_WINDOW_Y = 100
MAIN_WINDOW_WIDTH = 1200
MAIN_WINDOW_HEIGHT = 800

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
TASK_LIST_MARGINS = (10, 0, 16, 0)
TASK_LIST_SPACING = 10
TASK_LIST_MIN_WIDTH = 791
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
CENTRAL_WIDGET_STYLE = _style("""
QWidget#CentralWidget {
    background-color: $COLOR_SURFACE;
    border-radius: 0px;
}
""")

# Central widget style for maximized state.
CENTRAL_WIDGET_MAXIMIZED_STYLE = _style("""
QWidget#CentralWidget {
    background-color: $COLOR_SURFACE;
    border: none;
    border-radius: 0px;
}
""")

# Title-bar style.
TITLE_BAR_STYLE = _style("background: $COLOR_TRANSPARENT; border: none;")

# Minimize button style.
MINIMIZE_BUTTON_STYLE = _style("""
QPushButton {
    background-color: $COLOR_TRANSPARENT;
    color: $COLOR_ICON_MUTED;
    border-radius: 14px;
    font-weight: bold;
}
QPushButton:hover {
    background-color: $COLOR_TITLE_BAR_MINIMIZE_HOVER;
    color: $COLOR_TITLE_BAR_HOVER_ICON;
}
""")

# Close button style.
CLOSE_BUTTON_STYLE = _style("""
QPushButton {
    background-color: $COLOR_TRANSPARENT;
    color: $COLOR_ICON_MUTED;
    border-radius: 14px;
    font-weight: bold;
}
QPushButton:hover {
    background-color: $COLOR_TITLE_BAR_CLOSE_HOVER;
    color: $COLOR_TITLE_BAR_HOVER_ICON;
}
""")

# Maximize/restore button style.
MAXIMIZE_BUTTON_STYLE = _style("""
QPushButton {
    background-color: $COLOR_TRANSPARENT;
    color: $COLOR_ICON_MUTED;
    border-radius: 14px;
    font-weight: bold;
}
QPushButton:hover {
    background-color: $COLOR_TITLE_BAR_MAXIMIZE_HOVER;
    color: $COLOR_TITLE_BAR_HOVER_ICON;
}
""")

# URL input section style.
URL_INPUT_CONTAINER_STYLE = _style("""
QFrame {
    background-color: $COLOR_SURFACE_MUTED;
    border-radius: 10px;
}
""")

URL_INPUT_STYLE = _style("""
QLineEdit {
    border: 1px solid $COLOR_BORDER;
    border-radius: 8px;
    padding: 0 12px;
    background-color: $COLOR_SURFACE;
    color: $COLOR_TEXT_PRIMARY;
}
QLineEdit:focus {
    border: 1px solid $COLOR_ACCENT;
    background-color: $COLOR_SURFACE;
}
""")

# Download button style.
DOWNLOAD_BUTTON_STYLE = _style("""
QPushButton {
    background-color: $COLOR_ACCENT;
    color: $COLOR_ON_ACCENT;
    border: none;
    border-top-left-radius: 8px;
    border-bottom-left-radius: 8px;
}
QPushButton:hover { background-color: $COLOR_ACCENT_HOVER; }
QPushButton:pressed { background-color: $COLOR_ACCENT_PRESSED; }
QPushButton:disabled { background-color: $COLOR_CONTROL_SURFACE_ACTIVE; color: $COLOR_TEXT_DISABLED; }
""")

# Settings button style.
SETTINGS_BUTTON_STYLE = _style("""
QPushButton {
    background-color: $COLOR_CONTROL_SURFACE_EMPHASIS;
    color: $COLOR_TEXT_DEFAULT;
    border: none;
    border-top-right-radius: 8px;
    border-bottom-right-radius: 8px;
}
QPushButton:hover { background-color: $COLOR_CONTROL_SURFACE_EMPHASIS_HOVER; }
QPushButton:pressed { background-color: $COLOR_CONTROL_SURFACE_EMPHASIS_PRESSED; }
""")

# Status-bar style.
STATUS_BAR_STYLE = _style("background: $COLOR_TRANSPARENT;")

STATUS_LABEL_STYLE = _style("color: $COLOR_TEXT_SUBDUED;")

STATUS_COUNTER_STYLE = _style("color: $COLOR_TEXT_SUBDUED;")

STATUS_SORT_BUTTON_STYLE = _style("""
QToolButton {
    border: 1px solid $COLOR_BORDER;
    border-radius: 7px;
    padding: 0 5px;
    background-color: $COLOR_CONTROL_SURFACE;
    color: $COLOR_TEXT_DEFAULT;
    font-family: 'Segoe UI';
    font-size: 9pt;
}
QToolButton:hover {
    background-color: $COLOR_CONTROL_SURFACE_HOVER_STRONG;
    border-color: $COLOR_BORDER_HOVER;
}
QToolButton:pressed {
    background-color: $COLOR_CONTROL_SURFACE_PRESSED_STRONG;
    border-color: $COLOR_BORDER_PRESSED;
}
QToolButton::menu-indicator {
    image: none;
    width: 0px;
}
""")

STATUS_SORT_MENU_STYLE = _style("""
QMenu {
    background-color: $COLOR_SURFACE;
    border: 1px solid $COLOR_BORDER;
    border-radius: 6px;
    padding: 4px;
    color: $COLOR_TEXT_SECONDARY;
    font-family: 'Segoe UI';
    font-size: 9pt;
}
QMenu::item {
    padding: 6px 28px 6px 12px;
    border-radius: 4px;
}
QMenu::item:selected {
    background-color: $COLOR_MENU_SELECTION_SURFACE;
}
QMenu::indicator {
    width: 14px;
    height: 14px;
}
""")

# Task-card context menu style.
TASK_CONTEXT_MENU_STYLE = _style("""
QMenu {
    background-color: $COLOR_SURFACE;
    color: $COLOR_TEXT_PRIMARY;
    border: 1px solid $COLOR_BORDER;
    padding: 2px;
}
QMenu::item {
    padding: 5px 12px 5px 8px;
    border: none;
}
QMenu::item:selected {
    background-color: $COLOR_MENU_SELECTION_SURFACE;
}
QMenu::separator {
    height: 1px;
    background-color: $COLOR_DIVIDER;
    margin: 2px 4px;
}
""")

# Progress slider style.
PROGRESS_SLIDER_STYLE = _style("""
QSlider::groove:horizontal {
    border: none;
    background: $COLOR_BORDER;
    height: 4px;
    border-radius: 2px;
}
QSlider::sub-page:horizontal {
    background: $COLOR_PROGRESS_SLIDER_FILL;
    height: 4px;
    border-radius: 2px;
}
QSlider::handle:horizontal {
    width: 0px; 
    height: 0px; 
    margin: 0; 
    background: $COLOR_TRANSPARENT;
}
""")

# Task card style.
def get_card_style(color_hex, selected=False):
    """
    Build a card border style.
    
    Args:
        color_hex: Color code with or without a leading hash.
        selected: Whether the card is selected.
    """
    # Add a # prefix if it is missing.
    if not color_hex.startswith('#'):
        color_hex = '#' + color_hex
    
    # Define direct widget styles without selectors.
    if selected:
        # Selected state: changed background and emphasized border.
        return f"""
background-color: {_colors.COLOR_SELECTION_SURFACE};
border: 4px solid {_colors.COLOR_ACCENT};
border-radius: 8px;
"""
    else:
        return f"""
background-color: {_colors.COLOR_SURFACE};
border: 4px solid {color_hex};
border-radius: 8px;
"""

# Thumbnail label style.
# Thumbnail label style.
THUMBNAIL_LABEL_STYLE = _style("""
QLabel {
    background: $COLOR_CONTROL_SURFACE_ALT;
    border-radius: 4px;
    border: none;
    color: $COLOR_TEXT_MUTED;
}
""")

# Title label style.
TITLE_LABEL_STYLE = _style("""
QLabel {
    color: $COLOR_TEXT_PRIMARY;
    border: none;
    background: $COLOR_TRANSPARENT;
    font-family: 'Segoe UI';
    font-size: 11pt;
    font-weight: bold;
}
""")

# Uploader label style.
UPLOADER_LABEL_STYLE = _style("""
QLabel {
    color: $COLOR_TEXT_MUTED;
    border: none;
    background: $COLOR_TRANSPARENT;
    font-family: 'Segoe UI';
    font-size: 9pt;
}
""")

# Progress bar style.
PROGRESS_BAR_STYLE = _style("""
QProgressBar {
    border: none;
    background: $COLOR_PROGRESS_TRACK;
    border-radius: 3px;
}
QProgressBar::chunk {
    background-color: $COLOR_ACCENT;
    border-radius: 3px;
}
""")

# Progress bar style for finished state.
PROGRESS_BAR_FINISHED_STYLE = _style("""
QProgressBar { border: none; background: $COLOR_PROGRESS_TRACK; border-radius: 3px; }
QProgressBar::chunk { background-color: $COLOR_SUCCESS; border-radius: 3px; }
""")

# Progress bar style for error state.
PROGRESS_BAR_ERROR_STYLE = _style("""
QProgressBar { border: none; background: $COLOR_PROGRESS_TRACK; border-radius: 3px; }
QProgressBar::chunk { background-color: $COLOR_ERROR; border-radius: 3px; }
""")

# Percent label style.
# Percent label style.
PERCENT_LABEL_STYLE = _style("""
QLabel {
    color: $COLOR_ACCENT;
    border: none;
    background: $COLOR_TRANSPARENT;
    font-family: 'Segoe UI';
    font-size: 9pt;
    font-weight: bold;
}
""")

# Status label style, shared.
STATUS_LABEL_NORMAL_STYLE = _style("""
QLabel {
    color: $COLOR_TEXT_SUBDUED;
    border: none;
    background: $COLOR_TRANSPARENT;
    font-family: 'Segoe UI';
    font-size: 9pt;
}
""")

STATUS_LABEL_SUCCESS_STYLE = _style("""
QLabel {
    color: $COLOR_SUCCESS;
    font-weight: bold;
    border: none;
    background: $COLOR_TRANSPARENT;
    font-family: 'Segoe UI';
    font-size: 9pt;
}
""")

STATUS_LABEL_ERROR_STYLE = _style("""
QLabel {
    color: $COLOR_ERROR;
    font-weight: bold;
    border: none;
    background: $COLOR_TRANSPARENT;
    font-family: 'Segoe UI';
    font-size: 9pt;
}
""")

STATUS_LABEL_WARNING_STYLE = _style("""
QLabel {
    color: $COLOR_WARNING;
    font-weight: bold;
    border: none;
    background: $COLOR_TRANSPARENT;
    font-family: 'Segoe UI';
    font-size: 9pt;
}
""")

# Size label style.
SIZE_LABEL_STYLE = _style("""
QLabel {
    color: $COLOR_TEXT_FAINT;
    border: none;
    background: $COLOR_TRANSPARENT;
    font-family: 'Segoe UI';
    font-size: 9pt;
}
""")

# Action button style.
ACTION_BUTTON_STYLE = _style("""
QPushButton {
    background-color: $COLOR_CONTROL_SURFACE;
    border: 1px solid $COLOR_BORDER;
    border-radius: 6px;
    padding: 0px;
    margin: 0px;
}
QPushButton:hover { background-color: $COLOR_CONTROL_SURFACE_ACTIVE; }
QPushButton:pressed { background-color: $COLOR_CONTROL_SURFACE_PRESSED; }
""")

# Empty-state label style.
EMPTY_LABEL_STYLE = _style("color: $COLOR_TEXT_PLACEHOLDER; padding: 20px;")

# ===== Settings Dialog Style =====

# Settings dialog container style.
SETTINGS_CONTAINER_STYLE = _style("""
QFrame#Container {
    background-color: $COLOR_SURFACE;
    border: 1px solid $COLOR_BORDER;
    border-radius: 15px;
}
QLabel {
    font-family: 'Segoe UI', sans-serif;
    color: $COLOR_TEXT_PRIMARY;
}
""")

SETTINGS_CONTAINER_MAXIMIZED_STYLE = _style("""
QFrame#Container {
    background-color: $COLOR_SURFACE;
    border: none;
    border-radius: 0px;
}
QLabel {
    font-family: 'Segoe UI', sans-serif;
    color: $COLOR_TEXT_PRIMARY;
}
""")

# Settings dialog title label style.
SETTINGS_TITLE_LABEL_STYLE = _style("color: $COLOR_TEXT_PRIMARY;")

# Settings dialog close button style.
SETTINGS_CLOSE_BUTTON_STYLE = _style("""
QPushButton {
    background: $COLOR_TRANSPARENT;
    border: none;
    color: $COLOR_ICON_MUTED;
    border-radius: 12px;
    font-weight: bold;
}
QPushButton:hover {
    background-color: $COLOR_DANGER_SURFACE;
    color: $COLOR_DANGER;
}
""")

# Settings dialog section label style.
SETTINGS_SECTION_LABEL_STYLE = _style(
    "color: $COLOR_ACCENT; margin-top: 10px; margin-bottom: 5px;"
)

# Settings dialog regular label style.
SETTINGS_LABEL_STYLE = _style("color: $COLOR_TEXT_DEFAULT;")

# Settings dialog browse button style.
SETTINGS_BROWSE_BUTTON_STYLE = _style("""
QPushButton {
    background-color: $COLOR_CONTROL_SURFACE_ALT;
    border: 1px solid $COLOR_BORDER_STRONG;
    border-radius: 6px;
    padding: 0 10px;
    color: $COLOR_TEXT_DEFAULT;
    font-family: 'Segoe UI';
}
QPushButton:hover { background-color: $COLOR_CONTROL_SURFACE_ACTIVE; }
QPushButton:pressed { background-color: $COLOR_CONTROL_SURFACE_PRESSED; }
""")

# Settings dialog input field style.
SETTINGS_INPUT_STYLE = _style("""
QLineEdit, QSpinBox {
    border: 1px solid $COLOR_BORDER;
    border-radius: 6px;
    padding: 0 10px;
    background-color: $COLOR_SURFACE_SUBTLE;
    color: $COLOR_TEXT_PRIMARY;
    font-family: 'Segoe UI';
}
QSpinBox::up-button, QSpinBox::down-button {
    width: 20px;
}
""")

# Settings dialog combo-box style.
SETTINGS_COMBO_STYLE = _style("""
QComboBox {
    border: 1px solid $COLOR_BORDER;
    border-radius: 6px;
    padding: 0 34px 0 10px;
    background-color: $COLOR_SURFACE;
    color: $COLOR_TEXT_PRIMARY;
    font-family: 'Segoe UI';
}
QComboBox::drop-down {
    border: none;
    border-left: 1px solid $COLOR_BORDER;
    background-color: $COLOR_SURFACE_SUBTLE;
    width: 32px;
}
QComboBox::down-arrow {
    image: none;
    width: 0px;
    height: 0px;
}
""")

# Settings dialog numeric stepper style
SETTINGS_STEPPER_STYLE = _style("""
QWidget#SettingsStepper {
    background-color: $COLOR_SURFACE_SUBTLE;
    border: 1px solid $COLOR_BORDER;
    border-radius: 6px;
}
QPushButton#SettingsStepperButton {
    background-color: $COLOR_TRANSPARENT;
    border: none;
    border-radius: 6px;
}
QPushButton#SettingsStepperButton:hover {
    background-color: $COLOR_CONTROL_SURFACE_HOVER;
}
QPushButton#SettingsStepperButton:pressed {
    background-color: $COLOR_CONTROL_SURFACE_ACTIVE;
}
QPushButton#SettingsStepperButton:disabled {
    background-color: $COLOR_TRANSPARENT;
}
QLineEdit#SettingsStepperValue {
    color: $COLOR_TEXT_PRIMARY;
    font-family: 'Segoe UI';
    font-weight: bold;
    border: none;
    border-left: 1px solid $COLOR_BORDER;
    border-right: 1px solid $COLOR_BORDER;
    background-color: $COLOR_SURFACE;
    padding: 0;
}
QLineEdit#SettingsStepperValue:focus {
    border-left: 1px solid $COLOR_BORDER_STRONG;
    border-right: 1px solid $COLOR_BORDER_STRONG;
    background-color: $COLOR_SURFACE;
}
""")

# Settings dialog checkbox style
SETTINGS_CHECKBOX_STYLE = _style("""
QCheckBox {
    font-family: 'Segoe UI';
    font-size: 10pt;
    color: $COLOR_TEXT_PRIMARY;
    spacing: 5px;
}
QCheckBox::indicator {
    width: 18px;
    height: 18px;
}
""")

# Settings dialog cancel button style.
SETTINGS_CANCEL_BUTTON_STYLE = _style("""
QPushButton {
    background-color: $COLOR_CONTROL_SURFACE;
    color: $COLOR_TEXT_SUBDUED;
    border: none;
    border-radius: 8px;
    font-weight: bold;
    font-family: 'Segoe UI';
    padding: 0 8px;
}
QPushButton:hover { background-color: $COLOR_CONTROL_SURFACE_HOVER; }
""")

# Settings dialog save button style.
SETTINGS_SAVE_BUTTON_STYLE = _style("""
QPushButton {
    background-color: $COLOR_ACCENT;
    color: $COLOR_ON_ACCENT;
    border: none;
    border-radius: 8px;
    font-weight: bold;
    font-family: 'Segoe UI';
    padding: 0 8px;
}
QPushButton:hover { background-color: $COLOR_ACCENT_HOVER; }
QPushButton:pressed { background-color: $COLOR_ACCENT_PRESSED; }
""")

# Settings dialog tab style.
SETTINGS_TAB_STYLE = _style("""
QTabWidget::pane {
    border: 1px solid $COLOR_BORDER;
    border-radius: 5px;
    background: $COLOR_SURFACE;
}
QTabBar::tab {
    background: $COLOR_CONTROL_SURFACE;
    color: $COLOR_TEXT_SUBDUED;
    padding: 6px 10px;
    border: 1px solid $COLOR_BORDER;
    border-bottom: none;
    border-top-left-radius: 4px;
    border-top-right-radius: 4px;
    margin-right: 2px;
}
QTabBar::tab:selected {
    background: $COLOR_SURFACE;
    color: $COLOR_ACCENT;
    border-bottom: 1px solid $COLOR_SURFACE;
}
QTabBar::tab:hover:!selected {
    background: $COLOR_CONTROL_SURFACE_HOVER;
}
""")

# Settings dialog update/delete button style.
SETTINGS_UPDATE_BUTTON_STYLE = _style("""
QPushButton {
    background-color: $COLOR_CONTROL_SURFACE_ALT;
    border: 1px solid $COLOR_BORDER_UPDATE;
    border-radius: 5px;
    color: $COLOR_TEXT_PRIMARY;
    padding: 10px;
}
QPushButton:hover {
    background-color: $COLOR_CONTROL_SURFACE_ACTIVE;
}
""")

SETTINGS_UNINSTALL_BUTTON_STYLE = _style("""
QPushButton {
    background-color: $COLOR_DESTRUCTIVE_SURFACE;
    border: 1px solid $COLOR_DESTRUCTIVE_BORDER;
    border-radius: 5px;
    color: $COLOR_DANGER_STRONG;
    padding: 10px;
}
QPushButton:hover {
    background-color: $COLOR_DESTRUCTIVE_BORDER;
}
""")

# Login browser style.
LOGIN_BUTTON_BAR_STYLE = _style(
    "background-color: $COLOR_CONTROL_SURFACE; border-top: 1px solid $COLOR_BORDER;"
)
LOGIN_STATUS_NORMAL_STYLE = _style("color: $COLOR_TEXT_SUBDUED; border: none;")
LOGIN_STATUS_WARNING_STYLE = _style(
    "color: $COLOR_WARNING; font-weight: bold; border: none;"
)
LOGIN_STATUS_SUCCESS_STYLE = _style(
    "color: $COLOR_SUCCESS; font-weight: bold; border: none;"
)
LOGIN_STATUS_ERROR_STYLE = _style(
    "color: $COLOR_ERROR; font-weight: bold; border: none;"
)

# Download progress dialog style.
DETAIL_LABEL_STYLE = _style("color: $COLOR_TEXT_MUTED;")
INFO_LABEL_STYLE = _style("color: $COLOR_TEXT_FAINT;")

# Message dialog style.
MESSAGE_TITLE_STYLE = _style("color: $COLOR_TEXT_PRIMARY;")
MESSAGE_BODY_STYLE = _style("color: $COLOR_TEXT_SECONDARY;")
MESSAGE_DIVIDER_STYLE = _style("background-color: $COLOR_DIVIDER;")
