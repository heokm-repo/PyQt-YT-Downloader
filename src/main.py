"""
                    GNU GENERAL PUBLIC LICENSE
                       Version 3, 29 June 2007

 Copyright (C) 2026 Heo KyungMin

 This program is free software: you can redistribute it and/or modify
 it under the terms of the GNU General Public License as published by
 the Free Software Foundation, either version 3 of the License, or
 (at your option) any later version.

 This program is distributed in the hope that it will be useful,
 but WITHOUT ANY WARRANTY; without even the implied warranty of
 MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 GNU General Public License for more details.

 You should have received a copy of the GNU General Public License
 along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

import os
import sys

SUPPORTED_PLATFORM = 'win32'
UNSUPPORTED_PLATFORM_MESSAGE = (
    "YTDownloader is supported on Windows only. "
    "Please run this version on Windows 10 or later."
)


def is_supported_platform(platform_name=None):
    """Return True when the current runtime is supported."""
    return (platform_name or sys.platform) == SUPPORTED_PLATFORM


QApplication = QMessageBox = QDialog = None


def load_qt_widgets():
    """Import Qt widget classes after dependency checks have completed."""
    global QApplication, QMessageBox, QDialog
    if QApplication is None:
        from PyQt5.QtWidgets import (
            QApplication as _QApplication,
            QDialog as _QDialog,
            QMessageBox as _QMessageBox,
        )

        QApplication = _QApplication
        QMessageBox = _QMessageBox
        QDialog = _QDialog


try:
    current_dir = os.path.dirname(os.path.abspath(__file__))
    if current_dir not in sys.path:
        sys.path.insert(0, current_dir)
    from utils.logger import log
    from locales.strings import STR
    from constants import (
        APP_TITLE,
        ORGANIZATION_NAME,
        REQUIREMENTS_FILENAME,
        SRC_DIR_NAME,
    )
except ImportError:
    import logging

    log = logging.getLogger("YTDownloader")
    log.error = lambda msg, exc_info=None: print(f"ERROR: {msg}")
    log.warning = lambda msg, exc_info=None: print(f"WARNING: {msg}")
    log.info = lambda msg, exc_info=None: print(f"INFO: {msg}")
    log.debug = lambda msg, exc_info=None: print(f"DEBUG: {msg}")
    log.critical = lambda msg, exc_info=None: print(f"CRITICAL: {msg}")


def check_dependencies():
    """Check startup Python dependencies before constructing the GUI."""
    from startup.dependencies import check_dependencies as _check_dependencies

    return _check_dependencies()


def show_error_message(title, text, informative_text=""):
    """Show a startup error with MessageDialog when QApplication is available."""
    if QApplication is not None and QApplication.instance():
        try:
            from gui.dialogs.message_dialog import MessageDialog

            full_text = text
            if informative_text:
                full_text += f"\n\n{informative_text}"

            dialog = MessageDialog(title, full_text, MessageDialog.ERROR)
            dialog.exec_()
        except ImportError:
            from PyQt5.QtWidgets import QMessageBox

            msg = QMessageBox()
            msg.setIcon(QMessageBox.Critical)
            msg.setText(text)
            if informative_text:
                msg.setInformativeText(informative_text)
            msg.setWindowTitle(title)
            msg.exec_()
    else:
        print(f"[{title}] {text}")
        if informative_text:
            print(f"  {informative_text}")


def configure_startup_paths():
    """Configure import paths for the current startup environment."""
    from startup.paths import initialize_startup_paths

    return initialize_startup_paths(__file__, SRC_DIR_NAME)


def ensure_dependencies_or_exit():
    """Run startup dependency checks and display missing dependency errors."""
    from startup.dependencies import ensure_startup_dependencies

    return ensure_startup_dependencies(
        load_qt_widgets=load_qt_widgets,
        get_qapplication=lambda: QApplication,
        show_error_message=show_error_message,
        strings=STR,
        app_title=APP_TITLE,
        organization_name=ORGANIZATION_NAME,
        requirements_filename=REQUIREMENTS_FILENAME,
        logger=log,
        argv=sys.argv,
    )


def create_application(argv):
    """Create and configure the Qt application."""
    app = QApplication(argv)
    app.setApplicationName(APP_TITLE)
    app.setOrganizationName(ORGANIZATION_NAME)
    return app


def run_startup_flow():
    """Run binary initialization and self-update startup flows."""
    from startup.app_update import run_app_update_flow
    from startup.binary_flow import run_startup_binary_flow

    try:
        app_update_info = run_startup_binary_flow(
            QDialog.Accepted,
            show_error_message,
            log,
        )
        run_app_update_flow(
            app_update_info,
            QDialog.Accepted,
            QApplication,
            show_error_message,
            log,
        )
    except Exception as exc:
        log.error(f"Binary initialization error: {exc}", exc_info=True)
        show_error_message(
            STR.TITLE_INIT_FAIL,
            STR.ERR_INIT_GENERIC,
            f"오류: {str(exc)}",
        )
        sys.exit(1)


def create_main_window():
    """Import and construct the main window after startup has completed."""
    try:
        from gui.windows.main_window import YTDownloaderPyQt5
    except ImportError as exc:
        show_error_message(
            STR.TITLE_ERROR,
            STR.ERR_MODULE_IMPORT,
            STR.ERR_MODULE_HINT.format(error=str(exc)),
        )
        log.error(f"Import 오류: {exc}", exc_info=True)
        sys.exit(1)

    try:
        return YTDownloaderPyQt5()
    except Exception as exc:
        show_error_message(
            STR.TITLE_ERROR,
            STR.ERR_START_FAIL,
            f"오류: {str(exc)}",
        )
        log.error(f"윈도우 생성 오류: {exc}", exc_info=True)
        sys.exit(1)


def main():
    """Application entry point."""
    try:
        if not is_supported_platform():
            print(f"[Unsupported Platform] {UNSUPPORTED_PLATFORM_MESSAGE}")
            sys.exit(1)

        configure_startup_paths()
        ensure_dependencies_or_exit()
        load_qt_widgets()

        from startup.dependencies import import_optional_qt_webengine

        import_optional_qt_webengine(log)
        app = create_application(sys.argv)

        run_startup_flow()

        window = create_main_window()
        window.show()
        sys.exit(app.exec_())
    except Exception as exc:
        log.critical(f"치명적 오류: {exc}", exc_info=True)
        show_error_message(
            STR.TITLE_FATAL,
            STR.ERR_FATAL,
            f"오류: {str(exc)}",
        )
        sys.exit(1)


if __name__ == "__main__":
    main()
