from contextlib import nullcontext
from types import SimpleNamespace
from unittest.mock import Mock, patch

from data.duplicate_checker import DuplicateResult
from data.task_collection import TaskCollection
from gui.main_window.download_controller import DownloadController


def make_controller():
    view = SimpleNamespace(
        settings={'format': 'mp4'}, tasks=TaskCollection(), duplicate_checker=Mock(),
        status_label=Mock(), url_input=Mock(), download_btn=Mock(), history_manager=Mock(),
        on_playlist_analysis_finished=Mock(), _show_task_list=Mock(),
        _create_and_register_task=Mock(), total_tasks_in_queue=0, update_progress_ui=Mock())
    task_list = SimpleNamespace(closed=False, batch=nullcontext)
    return view, task_list, DownloadController(view, task_list)


def test_playlist_worker_keeps_qt_window_as_parent_and_public_completion_slot():
    view, _, controller = make_controller()
    with patch('gui.main_window.download_controller.stop_running_worker', return_value=SimpleNamespace(timed_out=False)), patch(
        'gui.main_window.download_controller.PlaylistAnalysisWorker'
    ) as factory:
        controller._handle_playlist_download('playlist-url')
    factory.assert_called_once_with('playlist-url', view)
    factory.return_value.analysis_finished.connect.assert_called_once_with(view.on_playlist_analysis_finished)
    factory.return_value.start.assert_called_once_with()


def test_single_confirmation_keeps_window_parent_and_cancellation():
    view, _, controller = make_controller()
    view.duplicate_checker.check.return_value = DuplicateResult(True)
    with patch('gui.main_window.download_controller.confirm_duplicate_overwrite_dialog', return_value=False) as confirm:
        controller._handle_single_video_download('url', 'id', 'youtube')
    assert confirm.call_args.args[0] is view
    view._create_and_register_task.assert_not_called()


def test_single_start_preserves_url_processing_and_registration_branch():
    view, _, controller = make_controller()
    view.url_input.text.return_value = '  https://example.invalid/id  '
    result = SimpleNamespace(is_playlist=False, clean_url='clean-url', video_id='id', extractor='Example')
    with patch('gui.main_window.download_controller.UrlProcessor') as urls, patch.object(
        controller, '_handle_single_video_download'
    ) as single:
        urls.requires_playlist_preference.return_value = False
        urls.process_url.return_value = result
        controller.start_download()
    urls.process_url.assert_called_once_with('https://example.invalid/id', prefer_playlist=False)
    single.assert_called_once_with('clean-url', 'id', 'Example')
    view.url_input.clear.assert_called_once_with()


def test_playlist_confirmation_preserves_new_input_multiplicity():
    view, _, controller = make_controller()
    view.history_manager.find_downloaded_ids.return_value = {'old'}
    with patch('gui.main_window.download_controller.ask_duplicate_confirmation_dialog', return_value=True) as confirm, patch.object(
        controller, '_register_playlist_tasks'
    ) as register:
        controller.on_playlist_analysis_finished('url', ['new', 'old', 'new'], True, '', 3)
    assert confirm.call_args.args[:3] == (view, 3, 1)
    register.assert_called_once_with(['new', 'new'])


def test_close_during_pre_registration_event_processing_stops_enqueue():
    view, task_list, controller = make_controller()

    def close():
        task_list.closed = True

    with patch('gui.main_window.download_controller.QApplication.processEvents', side_effect=close):
        controller._register_playlist_tasks(['one', 'two'])
    view._create_and_register_task.assert_not_called()
    assert view.total_tasks_in_queue == 0
    view.status_label.reset_mock()
    controller.on_playlist_analysis_finished('url', ['one'], True, '', 1)
    view.status_label.setText.assert_not_called()
