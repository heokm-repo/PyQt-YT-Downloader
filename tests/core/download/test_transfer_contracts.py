"""Transfer ownership and the intentionally different adapter failure policies."""
import hashlib
from pathlib import Path
from unittest.mock import Mock

import pytest
import requests

from utils import app_updater, download_stream


class Response:
    def __init__(self, chunks=(b'ab', b'', b'cd'), length='4', error=None):
        self.headers = {} if length is None else {'content-length': length}
        self.chunks = chunks
        self.error = error
        self.close = Mock()

    def raise_for_status(self):
        if self.error:
            raise self.error

    def iter_content(self, chunk_size):
        assert chunk_size == 8192
        for chunk in self.chunks:
            if isinstance(chunk, Exception):
                raise chunk
            yield chunk


@pytest.fixture
def transfer_env(monkeypatch, tmp_path):
    response = Response()
    request = Mock(return_value=response)
    monkeypatch.setattr(download_stream.requests, 'get', request)
    monkeypatch.setattr(app_updater, 'update_temp_dir', lambda: str(tmp_path))
    return response, request, tmp_path


def call_adapter(adapter, tmp_path, **kwargs):
    if adapter == 'binary':
        return download_stream.download_file('https://example.test/tool', str(tmp_path / 'tool'), **kwargs)
    return app_updater.download_update(
        'https://example.test/setup', expected_digest='sha256:' + hashlib.sha256(b'abcd').hexdigest(),
        **kwargs,
    )


def target(adapter, tmp_path):
    return tmp_path / ('tool' if adapter == 'binary' else app_updater.UPDATE_TEMP_FILENAME)


@pytest.mark.parametrize('adapter', ['binary', 'app'])
@pytest.mark.parametrize('length', [None, '0', '-1', '4'])
def test_lengths_empty_chunks_and_response_close(transfer_env, adapter, length):
    response, _, tmp_path = transfer_env
    response.headers = {} if length is None else {'content-length': length}
    progress = Mock()
    assert call_adapter(adapter, tmp_path, progress_callback=progress)
    assert target(adapter, tmp_path).read_bytes() == b'abcd'
    response.close.assert_called_once_with()
    if length != '4':
        progress.assert_not_called()
    elif adapter == 'binary':
        assert [call.args for call in progress.call_args_list] == [(2, 4), (4, 4)]
    else:
        assert progress.call_args.args == (100,)


@pytest.mark.parametrize('adapter', ['binary', 'app'])
@pytest.mark.parametrize('failure', ['http', 'read', 'write', 'header', 'callback'])
def test_failure_policy_and_close(transfer_env, monkeypatch, adapter, failure):
    response, _, tmp_path = transfer_env
    dest = target(adapter, tmp_path)
    dest.write_bytes(b'old')
    callback = None
    if failure == 'http':
        response.error = requests.HTTPError('503')
    elif failure == 'read':
        response.chunks = [b'ab', requests.ConnectionError('disconnected')]
    elif failure == 'write':
        real_open = open

        class FailingWriter:
            def __enter__(self):
                self.stream = real_open(dest, 'wb')
                return self

            def __exit__(self, *args):
                self.stream.close()

            def write(self, chunk):
                self.stream.write(chunk[:1])
                raise OSError('disk full')

        monkeypatch.setattr(download_stream, 'open', lambda *a, **k: FailingWriter(), raising=False)
    elif failure == 'header':
        response.headers['content-length'] = 'invalid'
    else:
        callback = Mock(side_effect=RuntimeError('callback failed'))

    if adapter == 'binary' and failure in ('header', 'callback'):
        with pytest.raises(ValueError if failure == 'header' else RuntimeError):
            call_adapter(adapter, tmp_path, progress_callback=callback)
    else:
        assert not call_adapter(adapter, tmp_path, progress_callback=callback)
    response.close.assert_called_once_with()
    if adapter == 'binary' and failure in ('write', 'header', 'callback'):
        assert dest.read_bytes() == {'write': b'a', 'header': b'old', 'callback': b'ab'}[failure]
    else:
        assert not dest.exists()


def test_precancel_does_not_request_or_remove_binary(transfer_env):
    response, request, tmp_path = transfer_env
    dest = target('binary', tmp_path)
    dest.write_bytes(b'existing')
    assert not call_adapter('binary', tmp_path, check_cancel=lambda: True)
    assert dest.read_bytes() == b'existing'
    request.assert_not_called()
    response.close.assert_not_called()


@pytest.mark.parametrize('adapter', ['binary', 'app'])
@pytest.mark.parametrize('cancel_at', ['empty', 'eof'])
def test_cancel_including_unknown_length_and_eof(transfer_env, adapter, cancel_at):
    response, _, tmp_path = transfer_env
    response.headers = {}
    state = {'cancel': False}

    def chunks(chunk_size):
        yield b'ab'
        if cancel_at == 'empty':
            state['cancel'] = True
            yield b''
            pytest.fail('transfer continued after cancellation')
        yield b'cd'
        state['cancel'] = True

    response.iter_content = chunks
    assert not call_adapter(adapter, tmp_path, check_cancel=lambda: state['cancel'])
    assert not target(adapter, tmp_path).exists()
    response.close.assert_called_once_with()


def test_app_requires_digest_before_request(transfer_env):
    _, request, _ = transfer_env
    assert app_updater.download_update('https://example.test/setup') is None
    request.assert_not_called()


def test_app_cancel_during_hash_removes_verified_file(transfer_env, monkeypatch):
    _, _, tmp_path = transfer_env
    state = {'cancel': False}

    def verify(path, digest):
        assert Path(path).read_bytes() == b'abcd'
        state['cancel'] = True
        return True

    monkeypatch.setattr(app_updater, 'verify_sha256', verify)
    assert call_adapter('app', tmp_path, check_cancel=lambda: state['cancel']) is None
    assert not target('app', tmp_path).exists()
