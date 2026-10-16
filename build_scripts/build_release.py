"""Build in an isolated workspace and publish the installer to output/."""
import argparse
from datetime import datetime, timezone
import os
from pathlib import Path
import shutil
import subprocess
import sys
from uuid import uuid4

from .release_inputs import ROOT, inventory, read_version, snapshot_inputs, verify_environment, write_manifest
from .build_process import run_logged


def find_iscc(explicit=None):
    if explicit:
        candidate = Path(explicit).resolve()
        if not candidate.is_file():
            raise FileNotFoundError(f'Inno Setup compiler not found: {candidate}')
        return candidate
    candidates = [Path(os.environ.get(name, '')) / 'Inno Setup 6/ISCC.exe'
                  for name in ('ProgramFiles(x86)', 'ProgramFiles')]
    found = shutil.which('ISCC.exe')
    if found:
        candidates.append(Path(found))
    return next((p.resolve() for p in candidates if p.is_file()), None)


def new_output(root, requested=None):
    releases = (root / 'build/releases').resolve()
    output = (requested or releases / (datetime.now().strftime('%Y%m%d-%H%M%S-') + uuid4().hex[:8])).resolve()
    if not output.is_relative_to(releases) or output == releases:
        raise ValueError('Build output must be a new child of build/releases')
    output.mkdir(parents=True, exist_ok=False)
    return output


def build(output, *, root=ROOT, iscc=None, skip_installer=False, run=run_logged):
    manifest = {'status': 'preparing', 'created_at_utc': datetime.now(timezone.utc).isoformat(),
                'installer': 'not built', 'installation_test': 'not performed', 'commands': []}
    manifest_path = output / 'manifest.json'
    try:
        print(f'[Prepare] Checking dependencies and snapshotting inputs: {output}', flush=True)
        manifest['environment'] = verify_environment(root)
        snapshot = output / 'snapshot'
        snapshot_inputs(root, snapshot)
        version = read_version(snapshot)
        manifest.update(version=version, inputs=inventory(snapshot))
        if not skip_installer and iscc is None:
            raise FileNotFoundError('Inno Setup is required; set ISCC_PATH or explicitly use --skip-installer')
        env = {**os.environ, 'PYINSTALLER_CONFIG_DIR': str(output / 'pyinstaller-cache'),
               'PYTHONDONTWRITEBYTECODE': '1', 'PYTHONUTF8': '1'}

        def execute(stage, command):
            manifest['status'] = stage
            manifest['commands'].append(command)
            write_manifest(manifest_path, manifest)
            print(f'[{stage}] Started. Log: {output / (stage + ".log")}', flush=True)
            with (output / (stage + '.log')).open('w', encoding='utf-8') as log:
                run(command, cwd=snapshot, env=env, stdout=log, stderr=subprocess.STDOUT, check=True)
            print(f'[{stage}] Completed.', flush=True)

        execute('pyinstaller', [sys.executable, '-B', '-m', 'PyInstaller', '--clean', '--noconfirm',
                '--distpath', str(output / 'dist'), '--workpath', str(output / 'work'),
                str(snapshot / 'YTDownloader.spec')])
        distribution = output / 'dist/YTDownloader'
        if not (distribution / 'YTDownloader.exe').is_file():
            raise RuntimeError('PyInstaller did not produce YTDownloader.exe')
        print('[Verify] Recording application file hashes...', flush=True)
        manifest['distribution'] = inventory(distribution)
        manifest['distribution_bytes'] = sum(item['bytes'] for item in manifest['distribution'])
        if not skip_installer:
            execute('installer', [str(iscc), '/DMyAppVersion=' + version,
                    '/DMyDistDir=' + str(distribution), '/DMyOutputDir=' + str(output / 'installer'),
                    str(snapshot / 'installer.iss')])
            installer = output / 'installer' / f'Setup_YTDownloader_v{version}.exe'
            if not installer.is_file():
                raise RuntimeError('Inno Setup did not produce the expected installer')
            manifest['installer'] = inventory(installer.parent)
            # Publish only a successful, freshly generated installer. A failed
            # build must leave the previous installer and output scripts intact.
            destination = root / 'output' / installer.name
            destination.parent.mkdir(parents=True, exist_ok=True)
            os.replace(installer, destination)
            manifest['installer_path'] = str(destination.resolve())
            print(f'[Publish] Installer saved: {destination}', flush=True)
        else:
            manifest['installer'] = 'explicitly skipped'
        manifest['status'] = 'built'
    except Exception as exc:
        manifest.update(status='failed', error=str(exc))
        raise
    finally:
        write_manifest(manifest_path, manifest)
    return manifest


def main():
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(errors='replace')
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, help='Fresh build workspace under build/releases; installer is saved in output/')
    parser.add_argument('--iscc', default=os.environ.get('ISCC_PATH'))
    parser.add_argument('--skip-installer', action='store_true')
    args = parser.parse_args()
    if sys.platform != 'win32':
        parser.error('Release builds require Windows (build.sh is for Windows Git Bash)')
    output = None
    try:
        output = new_output(ROOT, args.output)
        compiler = None if args.skip_installer else find_iscc(args.iscc)
        manifest = build(output, iscc=compiler, skip_installer=args.skip_installer)
    except Exception as exc:
        if output is not None and not (output / 'manifest.json').exists():
            write_manifest(output / 'manifest.json', {'status': 'failed', 'error': str(exc)})
        print(f'Build failed: {exc}', file=sys.stderr)
        return 1
    print(f'Build completed.\nBuild workspace: {output}\nManifest: {output / "manifest.json"}', flush=True)
    if manifest.get('installer_path'):
        print(f'Installer: {manifest["installer_path"]}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
