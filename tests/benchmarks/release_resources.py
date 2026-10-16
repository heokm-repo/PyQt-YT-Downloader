"""Audit disjoint resource groups in recorded builds, without removing files."""
import argparse
import json
from pathlib import Path


def summarize(manifest):
    records = manifest.get('distribution', manifest.get('artifacts', []))
    groups = {}
    for record in records:
        path = record['path'].lower()
        if '/qml/' in path:
            group = 'qt_qml'
        elif '/translations/' in path:
            group = 'qt_translations'
        elif '/qtawesome/' in path and ('/fonts/' in path or path.endswith('.ttf')):
            group = 'icon_fonts'
        elif '/pyqt5/' in path and ('webengine' in path or path.endswith('.pak')):
            group = 'qt_webengine'
        elif '/pyqt5/' in path:
            group = 'qt_other'
        else:
            group = 'other'
        item = groups.setdefault(group, {'bytes': 0, 'files': 0})
        item['bytes'] += record['bytes']
        item['files'] += 1
    return {'total_bytes': sum(item['bytes'] for item in records), 'total_files': len(records),
            'groups': groups, 'largest_files': sorted(records, key=lambda r: r['bytes'], reverse=True)[:10]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--current', type=Path, required=True)
    parser.add_argument('--baseline', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    data = {name: summarize(json.loads(path.read_text(encoding='utf-8')))
            for name, path in (('current', args.current), ('baseline', args.baseline))}
    data['difference_bytes'] = data['current']['total_bytes'] - data['baseline']['total_bytes']
    data['resource_exclusions_adopted'] = []
    args.output.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({k: {n: v for n, v in value.items() if n != 'largest_files'}
                      if isinstance(value, dict) else value for k, value in data.items()}))


if __name__ == '__main__':
    main()
