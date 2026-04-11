# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['src\\main.py'],
    pathex=['src'],
    binaries=[],
    datas=[],
    hiddenimports=['gui.windows.main_window', 'gui.windows.settings_dialog', 'gui.widgets.download_progress_dialog', 'core.workers', 'core.youtube_handler', 'core.ytdlp_wrapper', 'core.url_processor', 'core.scheduler', 'data.managers', 'data.models', 'gui.selection_manager', 'gui.context_menu', 'gui.task_actions', 'gui.widgets.task_item', 'gui.widgets.toggle_button', 'utils.logger', 'utils.utils', 'utils.bin_manager', 'utils.app_updater', 'utils.app_uninstaller', 'locales.ko', 'locales.ja', 'requests', 'urllib3', 'certifi', 'charset_normalizer', 'idna', 'packaging', 'packaging.version', 'packaging.specifiers', 'packaging.requirements'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    name='YTDownloader',
    exclude_binaries=True,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['app_icon.ico'],
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    name='YTDownloader',
)
