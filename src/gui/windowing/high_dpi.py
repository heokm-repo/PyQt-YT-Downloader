"""Qt display-scaling startup policy shared by application entry points."""


def configure_qt_display_policy(application_class, qt_namespace) -> None:
    """Keep Qt geometry in native pixels instead of logical DPI-scaled units."""
    application_class.setAttribute(qt_namespace.AA_DisableHighDpiScaling, True)
