"""Alternate fresh-process imports against a preserved source snapshot."""
import argparse
from pathlib import Path

from .environment import ROOT, environment_manifest, file_manifest, prepare_run, write_json
from .imports import IMPORT_SEQUENCES, import_sample
from .measurements import distribution


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--baseline-source', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--repeats', type=int, default=20)
    args = parser.parse_args()
    baseline = args.baseline_source.resolve()
    if not (baseline / 'main.py').is_file() or args.repeats < 20:
        parser.error('A preserved src directory and at least 20 repetitions are required')
    output = prepare_run(args.output)
    write_json(output / 'environment.json', environment_manifest())
    results = {'baseline_source': str(baseline), 'baseline_files': file_manifest(baseline, suffixes={'.py'}),
               'warmups_per_source': 1, 'repeats': args.repeats,
               'order': 'alternating baseline/current then current/baseline per iteration', 'imports': []}
    sources = {'baseline': baseline, 'current': ROOT / 'src'}
    for modules in IMPORT_SEQUENCES:
        samples = {name: {'import_ms': [], 'process_wall_ms': []} for name in sources}
        for iteration in range(args.repeats + 1):
            order = ('baseline', 'current') if iteration % 2 == 0 else ('current', 'baseline')
            for name in order:
                elapsed, wall = import_sample(sources[name], modules)
                if iteration:
                    samples[name]['import_ms'].append(elapsed)
                    samples[name]['process_wall_ms'].append(wall)
        results['imports'].append({'modules': modules, **{
            name: {key: distribution(values) for key, values in measurements.items()}
            for name, measurements in samples.items()}})
    write_json(output / 'results.json', results)
    print(f'Results: {output / "results.json"}')


if __name__ == '__main__':
    main()
