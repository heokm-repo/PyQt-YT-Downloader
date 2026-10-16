from pathlib import Path
from unittest.mock import Mock

import pytest

from utils.bin import executable_install, ffmpeg_download


@pytest.mark.parametrize('kind', ['executable', 'ffmpeg'])
def test_cancel_during_verification_never_installs_or_saves(monkeypatch, tmp_path, kind):
    state = {'cancel': False}
    downloaded = []
    install, save = Mock(), Mock()
    final = tmp_path / 'tool.exe'
    final.write_bytes(b'existing executable')

    def download(url, dest, progress, cancel):
        Path(dest).write_bytes(b'new executable')
        downloaded.append(Path(dest))
        return True

    def verify(path, digest):
        assert Path(path).read_bytes() == b'new executable'
        state['cancel'] = True
        return True

    module = executable_install if kind == 'executable' else ffmpeg_download
    monkeypatch.setattr(module, 'verify_sha256', verify)
    kwargs = dict(get_bin_path=lambda: str(tmp_path), download_file=download,
                  load_versions=Mock(return_value={}), save_versions=save,
                  check_cancel=lambda: state['cancel'], expected_digest='sha256:' + 'a' * 64)
    if kind == 'executable':
        monkeypatch.setattr(module, 'install_downloaded_binary', install)
        result = module.download_and_install_executable_binary(
            'tool', 'tool.exe', 'Tool', 'v2', 'offline', 'missing', **kwargs)
    else:
        result = module.download_and_install_ffmpeg_zip(
            'v2', 'offline', 'tool.exe', 'probe.exe', ('tool.exe',), ('probe.exe',),
            install_ffmpeg_from_zip=install, **kwargs)
    assert result is False
    install.assert_not_called()
    save.assert_not_called()
    assert final.read_bytes() == b'existing executable'
    assert len(downloaded) == 1 and not downloaded[0].exists()
