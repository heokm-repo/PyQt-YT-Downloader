"""Button specifications for the settings dialog."""

from dataclasses import dataclass


@dataclass(frozen=True)
class SettingsButtonSpec:
    label: str
    action: str
    style_key: str


def build_app_management_button_specs(
    check_update_text: str,
    license_text: str,
    sponsor_text: str,
    uninstall_text: str,
) -> list[SettingsButtonSpec]:
    """Return button specs for the app-management settings tab."""
    return [
        SettingsButtonSpec(check_update_text, "check_update", "update"),
        SettingsButtonSpec(license_text, "license", "update"),
        SettingsButtonSpec(sponsor_text, "sponsor", "update"),
        SettingsButtonSpec(uninstall_text, "uninstall", "uninstall"),
    ]


def build_dialog_action_button_specs(
    cancel_text: str,
    save_text: str,
) -> list[SettingsButtonSpec]:
    """Return button specs for the settings dialog footer."""
    return [
        SettingsButtonSpec(cancel_text, "cancel", "cancel"),
        SettingsButtonSpec(save_text, "save", "save"),
    ]