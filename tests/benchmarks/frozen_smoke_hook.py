"""Runtime hook for a SEPARATE diagnostic build. Never add to the shipping spec."""

import builtins
import json
import os
from pathlib import Path
import traceback

from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtWebEngineWidgets import QWebEnginePage, QWebEngineProfile, QWebEngineView
from PyQt5.QtWidgets import QApplication

from resources import styles
from startup import binary_flow
from utils import settings_store
from utils.bin import manager
import requests


smoke_root = Path(os.environ["YT_BENCHMARK_SMOKE_ROOT"]).resolve()
smoke_result = {"kind": "instrumented-frozen-smoke", "success": False,
                "mocked": ["startup release checks", "binary presence", "download worker startup"],
                "settings_reads": 0, "folder_probes": 0, "qss_activations": 0}


def write_result():
    (smoke_root / "smoke-result.json").write_text(
        json.dumps(smoke_result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


original_open = builtins.open
original_probe = settings_store._ensure_writable_folder
original_theme = styles.apply_theme


def counted_open(file, mode="r", *args, **kwargs):
    if isinstance(file, (str, os.PathLike)) and Path(file).name == "settings.json" and "r" in mode:
        smoke_result["settings_reads"] += 1
    return original_open(file, mode, *args, **kwargs)


def counted_probe(*args, **kwargs):
    smoke_result["folder_probes"] += 1
    return original_probe(*args, **kwargs)


def counted_theme(*args, **kwargs):
    smoke_result["qss_activations"] += 1
    return original_theme(*args, **kwargs)


def forbid_network(*args, **kwargs):
    raise AssertionError("Unexpected network request in frozen smoke")


builtins.open = counted_open
settings_store._ensure_writable_folder = counted_probe
styles.apply_theme = counted_theme
requests.sessions.Session.request = forbid_network
binary_flow.run_startup_checks = lambda: binary_flow.StartupCheckResult({}, (False, None, None, None))
manager.check_binary_presence = lambda: {"yt-dlp": True, "ffmpeg": True, "ffprobe": True, "qjs": True}

from gui.windows.main_window import YTDownloaderPyQt5

YTDownloaderPyQt5._initialize_scheduler = lambda self: None
original_show = YTDownloaderPyQt5.show


def run_checks(window):
    # Freeze startup counters before opening further dialogs or saving on close.
    builtins.open = original_open
    settings_store._ensure_writable_folder = original_probe
    styles.apply_theme = original_theme
    app = QApplication.instance()
    try:
        from gui.dialogs.init_setup_dialog import InitSetupDialog
        from gui.windows.settings_dialog import SettingsDialog
        import qtawesome
        from locales import get_language, set_language, SUPPORTED_LANGUAGES
        from locales.strings import STR

        language_before = get_language()
        smoke_result['languages'] = []
        for language in SUPPORTED_LANGUAGES:
            set_language(language)
            assert '{' not in STR.STATUS_FAILED_COUNT_FMT.format(done=1, total=2, message='reason')
            assert '{' not in STR.ERR_MEDIA_FINALIZATION_FMT.format(error='reason')
            smoke_result['languages'].append(language)
        set_language(language_before)

        smoke_result["qt_platform"] = app.platformName()
        smoke_result["font"] = app.font().family()
        smoke_result["main_window"] = window.windowTitle()
        smoke_result["icons"] = {}
        for name in ("mdi.play", "mdi6.hand-wave", "ri.play-fill"):
            pixmap = qtawesome.icon(name).pixmap(32, 32)
            smoke_result["icons"][name] = not pixmap.isNull()
            assert not pixmap.isNull(), name
        assert window.grab().save(str(smoke_root / "frozen-main.png"))
        for dialog, name in ((SettingsDialog(dict(window.settings), parent=window), "settings"),
                             (InitSetupDialog(parent=window), "initial-setup")):
            dialog.setAttribute(Qt.WA_DontShowOnScreen, True)
            dialog.show()
            app.processEvents()
            assert dialog.grab().save(str(smoke_root / f"frozen-{name}.png"))
            dialog.close()
            dialog.deleteLater()
        view = QWebEngineView(window)
        profile = QWebEngineProfile(view)  # Off-the-record local-page smoke; no login or network.
        page = QWebEnginePage(profile, view)
        view.setPage(page)
        window._smoke_webengine = (view, page, profile)
        completed = False

        def finish(success):
            nonlocal completed
            if completed:
                return
            completed = True
            smoke_result["webengine_local_html"] = bool(success)
            smoke_result["success"] = bool(success)
            write_result()
            page.deleteLater()
            view.deleteLater()
            window.close()
            app.exit(0 if success else 1)

        view.loadFinished.connect(finish)
        QTimer.singleShot(15000, lambda: finish(False))
        view.setHtml("<!doctype html><html><body>오프라인 기준 확인 ✓</body></html>")
    except Exception:
        smoke_result["error"] = traceback.format_exc()
        write_result()
        window.close()
        app.exit(1)


def smoke_show(window):
    window.setAttribute(Qt.WA_DontShowOnScreen, True)
    original_show(window)
    QTimer.singleShot(0, lambda: run_checks(window))


YTDownloaderPyQt5.show = smoke_show
