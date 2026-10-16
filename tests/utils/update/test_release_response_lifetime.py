from unittest.mock import Mock

import pytest
import requests

from utils import app_updater
from utils.bin import release_fetch


@pytest.mark.parametrize('kind', ['app', 'binary'])
@pytest.mark.parametrize('outcome', ['success', 'http', 'json', 'asset', 'digest'])
def test_strict_release_response_closed_for_all_results(monkeypatch, kind, outcome):
    digest = 'sha256:' + 'a' * 64
    asset = {'name': 'setup.exe', 'browser_download_url': 'https://example.test/setup', 'digest': digest}
    if outcome == 'digest':
        del asset['digest']
    response = Mock()
    response.json.return_value = {'tag_name': 'v999.0.0', 'assets': [] if outcome == 'asset' else [asset]}
    if outcome == 'http':
        response.raise_for_status.side_effect = requests.HTTPError('503')
    if outcome == 'json':
        response.json.side_effect = ValueError('invalid JSON')
    monkeypatch.setattr(requests, 'get', Mock(return_value=response))

    def parse(data):
        if not data['assets']:
            return None, None, None
        entry = data['assets'][0]
        return data['tag_name'], entry['browser_download_url'], entry.get('digest')

    if kind == 'app':
        check, error = app_updater.check_for_updates_strict, app_updater.AppUpdateCheckError
    else:
        check = lambda: release_fetch.check_latest_github_release_strict('offline', 'tool', parse, 'missing')
        error = release_fetch.ReleaseCheckError
    if outcome == 'success':
        assert check()
    else:
        with pytest.raises(error):
            check()
    response.close.assert_called_once_with()
