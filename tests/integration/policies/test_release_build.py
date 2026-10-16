import json
from pathlib import Path
import subprocess
import sys
from unittest.mock import Mock

import pytest

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from build_scripts import build_release, release_inputs


@pytest.fixture
def source(tmp_path, monkeypatch):
    root = tmp_path / 'project'
    (root / 'src').mkdir(parents=True)
    (root / 'src/constants.py').write_text("APP_VERSION = 'v2.3.3'\n", encoding='utf-8')
    for name in (*release_inputs.BUILD_FILES, 'build_scripts/build_release.py', 'build_scripts/build_process.py', 'build_scripts/release_inputs.py'):
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text('fixture', encoding='utf-8')
    monkeypatch.setattr(build_release, 'verify_environment', lambda _: {'fixture': True})
    return root


def test_output_refuses_existing_or_outside_paths_without_touching_files(source):
    for path in (source / 'dist', source / 'build', source / 'build/releases'):
        with pytest.raises(ValueError):
            build_release.new_output(source, path)
        assert not path.exists()
    created = build_release.new_output(source)
    sentinel = created / 'keep'
    sentinel.write_text('keep', encoding='utf-8')
    with pytest.raises(FileExistsError):
        build_release.new_output(source, created)
    assert sentinel.read_text(encoding='utf-8') == 'keep'


@pytest.mark.parametrize('value', ["APP_VERSION = 'v2.3.3'\nAPP_VERSION = unknown", "APP_VERSION = 'bad'", "APP_VERSION = 123"])
def test_invalid_version_never_runs_build_tools(source, value):
    (source / 'src/constants.py').write_text(value, encoding='utf-8')
    output = build_release.new_output(source)
    run = Mock()
    with pytest.raises(ValueError):
        build_release.build(output, root=source, skip_installer=True, run=run)
    run.assert_not_called()
    assert json.loads((output / 'manifest.json').read_text(encoding='utf-8'))['status'] == 'failed'


def test_pyinstaller_failure_never_runs_installer(source):
    output = build_release.new_output(source)
    run = Mock(side_effect=subprocess.CalledProcessError(7, 'PyInstaller'))
    with pytest.raises(subprocess.CalledProcessError):
        build_release.build(output, root=source, iscc=Path('ISCC.exe'), run=run)
    assert run.call_count == 1
    assert (output / 'snapshot/src/constants.py').is_file()
    assert json.loads((output / 'manifest.json').read_text(encoding='utf-8'))['status'] == 'failed'


def test_missing_compiler_does_not_silently_claim_success(source):
    output = build_release.new_output(source)
    run = Mock()
    with pytest.raises(FileNotFoundError):
        build_release.build(output, root=source, run=run)
    run.assert_not_called()


@pytest.mark.parametrize('installer_failure', [False, True])
def test_packaging_uses_only_new_outputs_and_records_hashes(source, installer_failure):
    output = build_release.new_output(source)
    published = source / 'output/Setup_YTDownloader_v2.3.3.exe'
    published.parent.mkdir()
    published.write_bytes(b'previous installer')
    script = source / 'output/publish.py'
    script.write_text('keep', encoding='utf-8')
    commands = []

    def run(command, **kwargs):
        commands.append(command)
        assert kwargs['check'] is True and kwargs['cwd'] == output / 'snapshot'
        if 'PyInstaller' in command:
            folder = Path(command[command.index('--distpath') + 1]) / 'YTDownloader'
            folder.mkdir(parents=True)
            (folder / 'YTDownloader.exe').write_bytes(b'application')
        elif installer_failure:
            raise subprocess.CalledProcessError(9, command)
        else:
            folder = output / 'installer'
            folder.mkdir()
            (folder / 'Setup_YTDownloader_v2.3.3.exe').write_bytes(b'installer')

    if installer_failure:
        with pytest.raises(subprocess.CalledProcessError):
            build_release.build(output, root=source, iscc=Path('ISCC.exe'), run=run)
    else:
        build_release.build(output, root=source, iscc=Path('ISCC.exe'), run=run)
    manifest = json.loads((output / 'manifest.json').read_text(encoding='utf-8'))
    assert manifest['status'] == ('failed' if installer_failure else 'built')
    assert len(commands) == 2 and len(manifest['distribution'][0]['sha256']) == 64
    assert not (source / 'dist').exists()
    assert script.read_text(encoding='utf-8') == 'keep'
    assert published.read_bytes() == (b'previous installer' if installer_failure else b'installer')
    if not installer_failure:
        assert manifest['installer_path'] == str(published.resolve())
        assert not (output / 'installer/Setup_YTDownloader_v2.3.3.exe').exists()
        import hashlib
        assert manifest['installer'][0]['sha256'] == hashlib.sha256(published.read_bytes()).hexdigest()


def test_dependency_mismatch_fails_before_build(tmp_path, monkeypatch):
    (tmp_path / 'constraints-build.txt').write_text('example==1.0\n', encoding='utf-8')
    monkeypatch.setattr(release_inputs.importlib.metadata, 'version', lambda _: '2.0')
    with pytest.raises(ValueError, match='expected 1.0'):
        release_inputs.verify_environment(tmp_path)
