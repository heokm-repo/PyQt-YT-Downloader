"""Validated settings are reused until first-run setup actually saves them."""
from types import SimpleNamespace
from unittest.mock import Mock, patch

import pytest

import main
from constants import KEY_LANGUAGE
from startup import binary_flow


@pytest.mark.parametrize('changed', [False, True])
def test_startup_reloads_only_after_initial_setup(changed):
    snapshot = {KEY_LANGUAGE: 'en'}
    saved = {KEY_LANGUAGE: 'ko'}
    result = binary_flow.StartupFlowResult((False, None, None, None), changed)
    with patch.object(main, 'QDialog', SimpleNamespace(Accepted=1)), patch(
        'startup.binary_flow.run_startup_binary_flow', return_value=result
    ) as flow, patch('startup.app_update.run_app_update_flow'), patch(
        'utils.settings_store.load_settings', return_value=saved
    ) as load:
        actual = main.run_startup_flow(snapshot)
    assert actual is (saved if changed else snapshot)
    assert flow.call_args.kwargs['initial_settings'] is snapshot
    assert load.call_count == int(changed)


def test_startup_language_uses_snapshot_without_folder_probe():
    with patch('utils.settings_store.load_settings') as load, patch('constants.change_language') as language:
        binary_flow.load_startup_language(Mock(), {KEY_LANGUAGE: 'ja'})
    load.assert_not_called()
    language.assert_called_once_with('ja')


def test_first_install_passes_snapshot_and_reports_settings_change():
    snapshot = {KEY_LANGUAGE: 'en'}
    checks = binary_flow.StartupCheckResult({}, (False, None, None, None))
    with patch.object(binary_flow, 'load_startup_language'), patch.object(
        binary_flow, 'run_startup_checks', return_value=checks
    ), patch('utils.bin.manager.check_binary_presence', return_value={'yt-dlp': False}), patch(
        'utils.bin.manager.missing_binary_downloads', return_value=('yt-dlp',)
    ), patch.object(binary_flow, 'run_initial_binary_install') as install:
        result = binary_flow.run_startup_binary_flow(1, Mock(), Mock(), initial_settings=snapshot)
    assert result.settings_changed
    assert install.call_args.kwargs['initial_settings'] is snapshot


def test_initial_setup_receives_validated_settings():
    snapshot = {KEY_LANGUAGE: 'en'}
    setup = Mock(return_value=SimpleNamespace(exec_=lambda: 1))
    progress = Mock(return_value=SimpleNamespace(exec_=lambda: 0, download_success=True))
    binary_flow.run_initial_binary_install(1, Mock(), Mock(), setup_dialog_factory=setup,
                                          progress_dialog_factory=progress, initial_settings=snapshot)
    setup.assert_called_once_with(initial_settings=snapshot)


def test_main_reads_settings_once_and_imports_webengine_before_application():
    snapshot = {KEY_LANGUAGE: 'en'}
    events = []
    app = Mock()
    app.exec_.return_value = 0
    with patch.object(main, 'is_supported_platform', return_value=True), patch.object(
        main, 'configure_startup_paths'
    ), patch('utils.app_restart.wait_for_restart_parent', return_value=True), patch.object(
        main, 'ensure_dependencies_or_exit'
    ), patch.object(main, 'load_qt_widgets'), patch(
        'startup.dependencies.import_optional_qt_webengine', side_effect=lambda log: events.append('webengine')
    ), patch.object(main, 'create_application', side_effect=lambda argv: events.append('application') or app), patch(
        'utils.settings_store.load_settings', return_value=snapshot
    ) as load, patch('gui.theme.apply_application_theme') as theme, patch.object(
        main, 'run_startup_flow', side_effect=lambda settings: settings
    ) as startup, patch.object(main, 'create_main_window') as window:
        with pytest.raises(SystemExit) as result:
            main.main()
    assert result.value.code == 0
    assert events == ['webengine', 'application']
    load.assert_called_once_with()
    theme.assert_called_once()
    startup.assert_called_once_with(snapshot)
    window.assert_called_once_with(snapshot)
