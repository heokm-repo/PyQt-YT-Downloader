"""Version parsing, source snapshots and inventories for Windows releases."""
import ast
import hashlib
import importlib.metadata
import json
from pathlib import Path
import platform
import re
import shutil
import sys

ROOT = Path(__file__).resolve().parents[1]
BUILD_FILES = ('YTDownloader.spec', 'app_icon.ico', 'requirements.txt', 'requirements-dev.txt',
               'constraints-build.txt', 'build.bat', 'build.sh', 'get_version.py', 'installer.iss', 'LICENSE')


def read_version(root=ROOT):
    tree = ast.parse((root / 'src/constants.py').read_text(encoding='utf-8'))
    values = [node.value for node in tree.body if isinstance(node, ast.Assign)
              and any(isinstance(t, ast.Name) and t.id == 'APP_VERSION' for t in node.targets)]
    if (len(values) != 1 or not isinstance(values[0], ast.Constant)
            or not isinstance(values[0].value, str)
            or not re.fullmatch(r'v?\d+\.\d+\.\d+(?:\.\d+)?', values[0].value)):
        raise ValueError('APP_VERSION must contain one literal numeric release version')
    return values[0].value.removeprefix('v')


def inventory(root):
    records = []
    for path in sorted(root.rglob('*')):
        if path.is_file() and '__pycache__' not in path.parts:
            with path.open('rb') as stream:
                digest = hashlib.file_digest(stream, 'sha256').hexdigest()
            records.append({'path': path.relative_to(root).as_posix(), 'bytes': path.stat().st_size,
                            'sha256': digest})
    return records


def snapshot_inputs(root, destination):
    destination.mkdir()
    sources = list((root / 'src').rglob('*.py')) + [root / name for name in BUILD_FILES]
    sources += [root / name for name in ('build_scripts/build_release.py', 'build_scripts/build_process.py', 'build_scripts/release_inputs.py')]
    for source in sources:
        target = destination / source.relative_to(root)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)


def verify_environment(root=ROOT):
    versions = {}
    for line in (root / 'constraints-build.txt').read_text(encoding='utf-8').splitlines():
        if not line.strip() or line.startswith('#'):
            continue
        package, expected = line.strip().split('==')
        actual = importlib.metadata.version(package)
        if actual != expected:
            raise ValueError(f'{package}: expected {expected}, installed {actual}; use constraints-build.txt')
        versions[package] = actual
    return {'python': sys.version, 'executable': sys.executable, 'platform': platform.platform(),
            'packages': versions}


def write_manifest(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
