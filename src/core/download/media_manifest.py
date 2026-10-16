"""Durable per-entry completion journal; stores no extracted download URLs."""
import hashlib
import json
import os
from pathlib import Path

from utils.json_store import read_json, write_json_atomic
from core.download.output_paths import verified_download_output_path


def completed_path(item, save_path):
    """Verify that the exact output recorded by this task still exists."""
    try:
        if item.get('state') != 'completed':
            return ''
        path = verified_download_output_path(item.get('output_path', ''), save_path)
        if path:
            stat = os.stat(path)
            if stat.st_size == item.get('size') and stat.st_mtime_ns == item.get('mtime_ns'):
                return path
    except (OSError, TypeError, ValueError):
        return ''
    return ''


def manifest_signature(url, settings):
    policy = {key: value for key, value in settings.items() if not key.startswith('_')}
    return hashlib.sha256(json.dumps([url, policy], sort_keys=True).encode('utf-8')).hexdigest()


def load_manifest(workspace, signature):
    path = Path(workspace, '.media_items.json')
    if not path.exists():
        return {}
    try:
        value = read_json(path)
        if value.get('signature') == signature and value.get('version') == 1:
            items = value.get('items', {})
            if isinstance(items, dict) and all(isinstance(item, dict) for item in items.values()):
                return items
    except (OSError, ValueError, AttributeError):
        return {}
    return {}


def save_manifest(workspace, signature, items):
    write_json_atomic(Path(workspace, '.media_items.json'), {
        'version': 1, 'signature': signature, 'items': items,
    })
