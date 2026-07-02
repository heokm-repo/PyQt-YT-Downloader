"""Startup dependency and optional QtWebEngine helpers."""
from __future__ import annotations

import sys
from typing import Any, Callable


def check_dependencies():
    """Check startup Python dependencies before constructing the GUI."""
    from utils.dependency_checker import check_startup_dependencies

    return check_startup_dependencies(include_optional=True)


def warn_optional_dependencies(report: Any, logger: Any) -> None:
    """Log optional dependency warnings without blocking startup."""
    if report.ok and report.missing_optional:
        logger.warning(
            f"Optional dependency missing: {report.format_missing_optional()}"
        )


def create_dependency_error_app(
    report: Any,
    load_qt_widgets: Callable[[], None],
    get_qapplication: Callable[[], Any],
    argv: list[str],
    app_title: str,
    organization_name: str,
    logger: Any,
) -> Any | None:
    """Create a minimal QApplication for dependency error dialogs when possible."""
    if report.is_missing_required("PyQt5"):
        return None

    try:
        load_qt_widgets()
        application = get_qapplication()
        if application.instance() is None:
            app = application(argv)
            app.setApplicationName(app_title)
            app.setOrganizationName(organization_name)
            return app
    except ImportError as exc:
        logger.debug(f"Qt fallback for dependency error is unavailable: {exc}")
    return None


def ensure_startup_dependencies(
    load_qt_widgets: Callable[[], None],
    get_qapplication: Callable[[], Any],
    show_error_message: Callable[[str, str, str], None],
    strings: Any,
    app_title: str,
    organization_name: str,
    requirements_filename: str,
    logger: Any,
    argv: list[str] | None = None,
) -> Any | None:
    """Validate dependencies and exit with a visible error if required ones are missing."""
    report = check_dependencies()
    warn_optional_dependencies(report, logger)
    if report.ok:
        return None

    app = create_dependency_error_app(
        report,
        load_qt_widgets,
        get_qapplication,
        sys.argv if argv is None else argv,
        app_title,
        organization_name,
        logger,
    )
    show_error_message(
        strings.TITLE_ERROR,
        strings.ERR_MISSING_DEP.format(module=report.format_missing_required()),
        strings.MSG_INSTALL_DEP.format(file=requirements_filename),
    )
    raise SystemExit(1) from None


def import_optional_qt_webengine(logger: Any) -> None:
    """Import QtWebEngine before QApplication is created when it is available."""
    try:
        from PyQt5 import QtWebEngineWidgets  # noqa: F401
    except ImportError:
        logger.debug("PyQtWebEngine is not installed; in-app login will be unavailable")
