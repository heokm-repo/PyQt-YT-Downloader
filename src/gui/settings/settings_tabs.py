"""Assemble the three settings tabs using the existing controls and policies."""
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QFormLayout, QVBoxLayout
from constants import (
    KEY_DOWNLOAD_FOLDER, KEY_VIDEO_QUALITY, KEY_AUDIO_QUALITY, KEY_FORMAT,
    KEY_MAX_DOWNLOADS, KEY_NORMALIZE_AUDIO, KEY_USE_ACCELERATION, KEY_LANGUAGE,
    KEY_THEME, KEY_UNIVERSAL_COMPATIBILITY, DEFAULT_MAX_DOWNLOADS,
    DEFAULT_ACCELERATION, DEFAULT_NORMALIZE, DEFAULT_THEME,
    DEFAULT_UNIVERSAL_COMPATIBILITY, VIDEO_QUALITY_OPTIONS, AUDIO_QUALITY_OPTIONS, APP_VERSION,
)
from locales.strings import STR
from resources import styles
from gui.settings.settings_general_rows import create_folder_picker_row, create_login_row
from gui.settings.settings_option_row import add_option_row
from gui.settings.settings_controls import (
    add_section_label, create_format_combo, create_language_combo, create_max_downloads_spin,
    create_settings_button, create_settings_checkbox, create_settings_combo,
    create_settings_label, create_theme_combo, create_version_row,
)
from gui.settings.settings_button_specs import build_app_management_button_specs


def create_general_tab(dialog, parent):
    """Create the general settings tab."""
    layout = QVBoxLayout(parent)
    layout.setContentsMargins(15, 15, 15, 15)
    layout.setSpacing(10)

    add_section_label(STR.SETTINGS_SEC_LOCATION, layout)
    folder_layout, dialog.folder_line, _ = create_folder_picker_row(
        dialog.settings[KEY_DOWNLOAD_FOLDER],
        STR.SETTINGS_BTN_BROWSE,
        dialog._browse_folder,
    )
    layout.addLayout(folder_layout)

    add_section_label(STR.SETTINGS_SEC_GENERAL, layout)
    lang_form_layout = QFormLayout()
    lang_form_layout.setSpacing(10)
    lang_form_layout.setLabelAlignment(Qt.AlignLeft)

    dialog.language_combo = create_language_combo(
        dialog.settings.get(KEY_LANGUAGE)
    )
    lang_form_layout.addRow(create_settings_label(STR.SETTINGS_LABEL_LANGUAGE), dialog.language_combo)

    dialog.theme_combo = create_theme_combo(
        dialog.settings.get(KEY_THEME, DEFAULT_THEME),
        STR.SETTINGS_THEME_LIGHT,
        STR.SETTINGS_THEME_DARK,
    )
    lang_form_layout.addRow(
        create_settings_label(STR.SETTINGS_LABEL_THEME),
        dialog.theme_combo,
    )
    layout.addLayout(lang_form_layout)

    cookie_layout = create_login_row(
        STR.SETTINGS_LABEL_COOKIES,
        STR.BTN_LOGIN,
        dialog._on_login_clicked,
        STR.BTN_LOGOUT,
        dialog._on_logout_clicked,
    )
    layout.addLayout(cookie_layout)
    layout.addStretch()


def create_download_tab(dialog, parent):
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
    dialog.quality_combo = create_settings_combo(
        VIDEO_QUALITY_OPTIONS,
        dialog.settings[KEY_VIDEO_QUALITY]
    )
    grid_layout.addRow(create_settings_label(STR.SETTINGS_LABEL_VIDEO), dialog.quality_combo)

    # Audio quality.
    dialog.audio_quality_combo = create_settings_combo(
        AUDIO_QUALITY_OPTIONS,
        dialog.settings[KEY_AUDIO_QUALITY]
    )
    grid_layout.addRow(create_settings_label(STR.SETTINGS_LABEL_AUDIO), dialog.audio_quality_combo)

    # Format.
    dialog.format_combo = create_format_combo(
        dialog.settings.get(KEY_FORMAT),
        STR.SETTINGS_HEADER_VIDEO,
        STR.SETTINGS_HEADER_AUDIO,
    )
    dialog.format_combo.currentTextChanged.connect(dialog._on_format_changed)
    grid_layout.addRow(create_settings_label(STR.SETTINGS_LABEL_FORMAT), dialog.format_combo)

    # Maximum concurrent downloads.
    dialog.max_downloads_spin = create_max_downloads_spin(
        int(dialog.settings.get(KEY_MAX_DOWNLOADS, DEFAULT_MAX_DOWNLOADS))
    )
    grid_layout.addRow(create_settings_label(STR.SETTINGS_LABEL_MAX_DL), dialog.max_downloads_spin)

    layout.addLayout(grid_layout)

    # Advanced features.
    add_section_label(STR.SETTINGS_SEC_ADVANCED, layout)

    # Audio normalization.
    dialog.norm_check = create_settings_checkbox(
        dialog.settings.get(KEY_NORMALIZE_AUDIO, DEFAULT_NORMALIZE)
    )
    add_option_row(
        layout, STR.SETTINGS_CHK_NORMALIZE, STR.TOOLTIP_NORMALIZE, dialog.norm_check
    )

    # Universal compatibility.
    dialog.compatibility_check = create_settings_checkbox(
        dialog.settings.get(
            KEY_UNIVERSAL_COMPATIBILITY,
            DEFAULT_UNIVERSAL_COMPATIBILITY,
        ),
        lambda state: dialog._on_compatibility_changed(state == 2),
    )
    add_option_row(
        layout,
        STR.SETTINGS_CHK_COMPATIBILITY,
        STR.TOOLTIP_COMPATIBILITY,
        dialog.compatibility_check,
    )

    # Download acceleration.
    dialog.accel_check = create_settings_checkbox(
        dialog.settings.get(KEY_USE_ACCELERATION, DEFAULT_ACCELERATION),
        lambda state: dialog._on_acceleration_changed(state == 2),
    )
    add_option_row(
        layout, STR.SETTINGS_CHK_ACCEL, STR.TOOLTIP_ACCEL, dialog.accel_check
    )

    # Apply initial state.
    dialog._on_format_changed(dialog.format_combo.currentText())
    dialog._on_compatibility_changed(dialog.compatibility_check.isChecked())
    dialog._on_acceleration_changed(dialog.accel_check.isChecked())

    layout.addStretch()


def create_app_manage_tab(dialog, parent):
    """Create the app-management tab."""
    layout = QVBoxLayout(parent)
    layout.setContentsMargins(15, 15, 15, 15)
    layout.setSpacing(15)

    add_section_label(STR.SETTINGS_SEC_APP_MANAGE, layout)

    layout.addLayout(
        create_version_row(STR.SETTINGS_LABEL_VERSION, APP_VERSION)
    )

    button_styles = {
        "update": styles.SETTINGS_UPDATE_BUTTON_STYLE,
        "uninstall": styles.SETTINGS_UNINSTALL_BUTTON_STYLE,
    }
    button_callbacks = {
        "check_update": dialog._on_check_update_clicked,
        "license": dialog._show_license_info,
        "sponsor": dialog._open_sponsor_page,
        "uninstall": dialog._on_uninstall_clicked,
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
            dialog.update_check_button = button
        layout.addWidget(button)

    layout.addStretch()
