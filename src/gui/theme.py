"""Application-wide theme activation and Qt palette construction."""

from PyQt5.QtGui import QColor, QPalette
from PyQt5.QtWidgets import QApplication

from resources import colors, styles


def build_qt_palette() -> QPalette:
    """Build a Qt palette from the currently active semantic colors."""
    palette = QPalette()
    roles = {
        QPalette.Window: colors.COLOR_SURFACE,
        QPalette.WindowText: colors.COLOR_TEXT_PRIMARY,
        QPalette.Base: colors.COLOR_SURFACE,
        QPalette.AlternateBase: colors.COLOR_SURFACE_SUBTLE,
        QPalette.ToolTipBase: colors.COLOR_SURFACE_SUBTLE,
        QPalette.ToolTipText: colors.COLOR_TEXT_PRIMARY,
        QPalette.Text: colors.COLOR_TEXT_PRIMARY,
        QPalette.Button: colors.COLOR_CONTROL_SURFACE,
        QPalette.ButtonText: colors.COLOR_TEXT_PRIMARY,
        QPalette.BrightText: colors.COLOR_DANGER,
        QPalette.Link: colors.COLOR_INFO,
        QPalette.Highlight: colors.COLOR_ACCENT,
        QPalette.HighlightedText: colors.COLOR_ON_ACCENT,
    }
    for role, color in roles.items():
        palette.setColor(role, QColor(color))

    palette.setColor(
        QPalette.Disabled,
        QPalette.WindowText,
        QColor(colors.COLOR_TEXT_DISABLED),
    )
    palette.setColor(
        QPalette.Disabled,
        QPalette.Text,
        QColor(colors.COLOR_TEXT_DISABLED),
    )
    palette.setColor(
        QPalette.Disabled,
        QPalette.ButtonText,
        QColor(colors.COLOR_TEXT_DISABLED),
    )
    return palette


def apply_application_theme(theme_name: str | None) -> str:
    """Activate theme colors, rebuild QSS, and update the QApplication palette."""
    active_theme = styles.apply_theme(theme_name)
    app = QApplication.instance()
    if app is not None:
        app.setPalette(build_qt_palette())
    return active_theme
