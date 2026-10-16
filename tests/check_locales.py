"""Audit locale completeness without loading the application or changing its language."""
import argparse
import ast
from collections import Counter
import json
from pathlib import Path
from string import Formatter

ROOT = Path(__file__).resolve().parents[1]


def read_tree(path):
    return ast.parse(path.read_text(encoding='utf-8'), filename=str(path))


def read_dictionary(path, name):
    tree = read_tree(path)
    node = next(n.value for n in tree.body if isinstance(n, ast.Assign)
                and any(isinstance(t, ast.Name) and t.id == name for t in n.targets))
    pairs = [(ast.literal_eval(k), ast.literal_eval(v)) for k, v in zip(node.keys, node.values)]
    duplicates = sorted(k for k, count in Counter(k for k, _ in pairs).items() if count > 1)
    return dict(pairs), duplicates


def english_defaults(root=ROOT):
    pairs = []
    for name in ('strings.py', 'runtime_strings.py'):
        for node in ast.walk(read_tree(root / 'src/locales' / name)):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == 'get_string':
                pairs.append(tuple(ast.literal_eval(arg) for arg in node.args[:2]))
    return pairs


def format_fields(text):
    """Include repeated fields, conversions and nested width/precision fields."""
    fields = []
    for _, field, spec, conversion in Formatter().parse(text):
        if field is not None:
            fields.append((field, spec, conversion))
            fields.extend(format_fields(spec))
    return sorted(fields, key=repr)


def audit_locales(root=ROOT):
    issues = []
    pairs = english_defaults(root)
    defaults = dict(pairs)
    for key, count in Counter(k for k, _ in pairs).items():
        if count > 1:
            issues.append(f'en: duplicate key {key}')
    languages, _ = read_dictionary(root / 'src/locales/__init__.py', 'SUPPORTED_LANGUAGES')
    counts = {}
    for language in languages:
        if language == 'en':
            values, duplicates = defaults, []
        else:
            path = root / 'src/locales' / (language.lower().replace('-', '_') + '.py')
            values, duplicates = read_dictionary(path, 'STRINGS')
        counts[language] = len(values)
        issues.extend(f'{language}: duplicate key {k}' for k in duplicates)
        issues.extend(f'{language}: missing key {k}' for k in sorted(defaults.keys() - values.keys()))
        issues.extend(f'{language}: unknown key {k}' for k in sorted(values.keys() - defaults.keys()))
        for key, value in values.items():
            if not isinstance(value, str) or not value.strip():
                issues.append(f'{language}: empty/non-string value {key}')
                continue
            if key not in defaults:
                continue
            try:
                if format_fields(value) != format_fields(defaults[key]):
                    issues.append(f'{language}: format fields differ for {key}')
            except ValueError as exc:
                issues.append(f'{language}: invalid format for {key}: {exc}')
    for path in (root / 'src').rglob('*.py'):
        for node in ast.walk(read_tree(path)):
            if (isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name)
                    and node.value.id == 'STR' and node.attr not in defaults):
                issues.append(f'{path.relative_to(root)}:{node.lineno}: undefined STR.{node.attr}')
    return {'key_count': len(defaults), 'languages': counts, 'issues': issues}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    result = audit_locales()
    text = json.dumps(result, ensure_ascii=False, indent=2) + '\n'
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding='utf-8')
    print(text, end='')
    return int(bool(result['issues']))


if __name__ == '__main__':
    raise SystemExit(main())
