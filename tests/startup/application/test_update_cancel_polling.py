from unittest.mock import Mock

from startup import app_update
from utils import app_updater, download_stream


def test_unknown_length_transfer_pumps_events_and_cancels(monkeypatch, tmp_path):
    now, cancelled, read_chunks = [0.0], [False], []
    dialog = Mock()
    dialog.was_cancelled.side_effect = lambda: cancelled[0]

    def process_events():
        if now[0] >= 0.05:
            cancelled[0] = True

    response = Mock()
    response.headers = {}

    def chunks(chunk_size):
        for index in range(100):
            now[0] += 0.02
            read_chunks.append(index)
            yield b'x'

    response.iter_content.side_effect = chunks
    monkeypatch.setattr(app_update.time, 'monotonic', lambda: now[0])
    monkeypatch.setattr(download_stream.requests, 'get', Mock(return_value=response))
    monkeypatch.setattr(app_updater, 'update_temp_dir', lambda: str(tmp_path))
    result = app_update.download_app_update(
        'offline', app_updater.download_update, Mock(processEvents=process_events), Mock(),
        progress_dialog_factory=lambda **kwargs: dialog, expected_digest='sha256:' + 'a' * 64,
    )
    assert result is None
    assert len(read_chunks) == 3
    dialog.set_progress.assert_not_called()
    dialog.mark_installing.assert_not_called()
    dialog.close.assert_called_once_with()
    response.close.assert_called_once_with()
    assert not (tmp_path / app_updater.UPDATE_TEMP_FILENAME).exists()
