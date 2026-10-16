"""Exercise requests' real response/file lifecycle against loopback HTTP."""
import hashlib
from http.server import BaseHTTPRequestHandler, HTTPServer
from threading import Thread
from unittest.mock import Mock

import pytest

from utils import app_updater, download_stream


@pytest.mark.parametrize('adapter', ['binary', 'app'])
@pytest.mark.parametrize('known_length', [False, True])
@pytest.mark.parametrize('cancel', [False, True])
def test_real_http_bytes_and_cancellation(monkeypatch, tmp_path, adapter, known_length, cancel):
    payload = bytes(range(256)) * 256

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            if known_length:
                self.send_header('Content-Length', str(len(payload)))
            self.end_headers()
            try:
                self.wfile.write(payload)
            except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
                pass  # The client may cancel while the server is still writing.

        def log_message(self, *args):
            pass

    server = HTTPServer(('127.0.0.1', 0), Handler)
    thread = Thread(target=lambda: server.serve_forever(poll_interval=0.01))
    thread.start()
    responses = []
    original_get = download_stream.requests.get

    def get(*args, **kwargs):
        response = original_get(*args, **kwargs)
        response.close = Mock(wraps=response.close)
        responses.append(response)
        return response

    checks = []

    def check_cancel():
        checks.append(True)
        return cancel and len(checks) == 4

    monkeypatch.setattr(download_stream.requests, 'get', get)
    monkeypatch.setattr(app_updater, 'update_temp_dir', lambda: str(tmp_path))
    url = f'http://127.0.0.1:{server.server_port}/fixture'
    try:
        if adapter == 'binary':
            path = tmp_path / 'tool'
            result = download_stream.download_file(url, str(path), check_cancel=check_cancel)
        else:
            path = tmp_path / app_updater.UPDATE_TEMP_FILENAME
            result = app_updater.download_update(
                url, expected_digest='sha256:' + hashlib.sha256(payload).hexdigest(),
                check_cancel=check_cancel,
            )
        assert bool(result) is not cancel
        assert len(responses) == 1
        responses[0].close.assert_called_once_with()
        assert responses[0].raw.closed
        if cancel:
            assert len(checks) == 4
            assert not path.exists()
        else:
            assert path.read_bytes() == payload
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)
        assert not thread.is_alive()
