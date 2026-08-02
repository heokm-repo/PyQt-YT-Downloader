"""Live theme refresh helpers for the main window and its existing children."""

import qtawesome as qta

from gui.main_window.controls import set_button_icon
from resources import colors, styles


def apply_main_window_theme(window) -> None:
    """Reapply the active theme to an already constructed main window."""
    window.setStyleSheet(styles.MAIN_WINDOW_STYLE)
    window._apply_window_chrome_state(window._is_maximized_state)

    window.title_bar_frame.setStyleSheet(styles.TITLE_BAR_STYLE)
    window.app_title_label.setStyleSheet(f"color: {colors.COLOR_ACCENT};")
    window.minimize_btn.setStyleSheet(styles.MINIMIZE_BUTTON_STYLE)
    window.maximize_btn.setStyleSheet(styles.MAXIMIZE_BUTTON_STYLE)
    window.close_btn.setStyleSheet(styles.CLOSE_BUTTON_STYLE)
    set_button_icon(
        window.minimize_btn,
        "mdi.window-minimize",
        hover_color=colors.COLOR_TITLE_BAR_HOVER_ICON,
    )
    set_button_icon(
        window.close_btn,
        "mdi.window-close",
        hover_color=colors.COLOR_TITLE_BAR_HOVER_ICON,
    )

    window.url_section_frame.setStyleSheet(styles.URL_INPUT_CONTAINER_STYLE)
    window.toggle_btn.update_icon()
    window.url_input.setStyleSheet(styles.URL_INPUT_STYLE)
    window.download_btn.setStyleSheet(styles.DOWNLOAD_BUTTON_STYLE)
    window.settings_btn.setIcon(
        qta.icon("mdi.cog", color=colors.COLOR_ICON_DEFAULT)
    )
    window.settings_btn.setStyleSheet(styles.SETTINGS_BUTTON_STYLE)

    transparent_style = f"background: {colors.COLOR_TRANSPARENT}; border: none;"
    window.scroll_area.setStyleSheet(transparent_style)
    window.scroll_content.setStyleSheet(
        f"background: {colors.COLOR_TRANSPARENT};"
    )
    window.empty_label.setStyleSheet(styles.EMPTY_LABEL_STYLE)

    window.status_bar_frame.setStyleSheet(styles.STATUS_BAR_STYLE)
    window.task_sort_button.apply_theme()
    window.status_label.setStyleSheet(styles.STATUS_LABEL_STYLE)
    window.progress_slider.setStyleSheet(styles.PROGRESS_SLIDER_STYLE)
    window.task_counter_label.setStyleSheet(styles.STATUS_COUNTER_STYLE)

    for task_widget in window.task_widgets.values():
        task_widget.apply_theme()

    window.update()
