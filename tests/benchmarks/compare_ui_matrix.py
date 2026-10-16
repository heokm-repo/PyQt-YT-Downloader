"""Run preserved/current locale-theme matrices in fresh processes at three scales."""
import argparse
import json
from pathlib import Path
import subprocess
import sys

from .environment import ROOT, prepare_run, write_json


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--baseline-source', type=Path, required=True)
    args = parser.parse_args()
    output = prepare_run(args.output)
    baseline = args.baseline_source.resolve()
    if not (baseline / 'main.py').is_file():
        parser.error('Expected a preserved src directory')
    comparisons = []
    for scale, label in (('1', '100'), ('1.5', '150'), ('2', '200')):
        for kind, source in (('baseline', baseline), ('current', ROOT / 'src')):
            subprocess.run([sys.executable, '-B', '-m', 'tests.benchmarks.ui_matrix',
                            '--output', str(output / f'{kind}-{label}'), '--source', str(source),
                            '--scale', scale], check=True)
        from PyQt5.QtGui import QImage
        before, after = output / f'baseline-{label}', output / f'current-{label}'
        before_results = json.loads((before / 'results.json').read_text(encoding='utf-8'))
        after_results = json.loads((after / 'results.json').read_text(encoding='utf-8'))
        files = sorted((before / 'screenshots').glob('*.png'))
        assert {p.name for p in files} == {p.name for p in (after / 'screenshots').glob('*.png')}
        differences = [p.name for p in files if QImage(str(p)) != QImage(str(after / 'screenshots' / p.name))]
        comparisons.append({'scale': scale, 'dpr': after_results['dpr'], 'images': len(files),
                            'different_images': differences,
                            'baseline_clipping': [c for c in before_results['cases'] if c['clipping']],
                            'current_clipping': [c for c in after_results['cases'] if c['clipping']]})
        write_json(output / 'comparison.json', comparisons)
        print(f'Matrix {label}: {len(files)} pairs, {len(differences)} differences', flush=True)
    if any(c['different_images'] or c['current_clipping'] != c['baseline_clipping'] for c in comparisons):
        raise SystemExit('Inspect recorded pixel/clipping differences')


if __name__ == '__main__':
    main()
