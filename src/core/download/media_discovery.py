"""Resolve a URL into ordered media entries without treating unknowns as photos."""
from dataclasses import dataclass
import json
from pathlib import Path
import tempfile
from urllib.parse import urlsplit

from core.download.options import _add_runtime_extract_options
from locales.strings import STR
from utils.logger import log


@dataclass
class MediaEntry:
    key: str
    info: dict
    kind: str


def image_ids_from_responses(directory):
    """Use explicit Instagram media types, never an empty formats heuristic.

    Only JSON response dumps from this exact extraction are inspected. Dumps are
    temporary; neither response bodies nor signed media URLs enter task storage.
    """
    images = set()

    def visit(value):
        if isinstance(value, dict):
            code = value.get('code') or value.get('shortcode')
            if code and (value.get('media_type') == 1 or value.get('__typename') in (
                'GraphImage', 'XIGPolarisImageMedia'
            )):
                images.add(str(code))
            for child in value.values():
                visit(child)
        elif isinstance(value, list):
            for child in value:
                visit(child)

    for path in Path(directory).glob('*.dump'):
        try:
            visit(json.loads(path.read_text(encoding='utf-8')))
        except (OSError, ValueError, RecursionError):
            continue
    return images


def classify_entry(info, image_ids=()):
    if str(info.get('id')) in image_ids or info.get('_type') == 'image':
        return 'image'
    formats = info.get('formats')
    if formats:
        return 'media'
    if info.get('_type', 'video') == 'video' and info.get('url') and info.get('ext') in (
        'mp4', 'webm', 'mkv', 'mov', 'm4a', 'mp3', 'wav', 'ogg', 'opus', 'flac',
    ):
        return 'media'
    return 'unknown'


def discover_media(wrapper, url, settings, workspace, stop_check=None):
    """Resolve nested playlists/URL results; return parent metadata and entries.

    A missing/failed entry is retained as unknown so it cannot silently disappear
    from completion accounting. Authentication and extraction failures stay errors.
    """
    entries, resolving, seen_keys = [], set(), set()

    def extract(target):
        if stop_check and stop_check():
            raise InterruptedError('Media discovery cancelled')
        host = (urlsplit(target).hostname or '').lower()
        instagram = host == 'instagram.com' or host.endswith('.instagram.com')
        options = _add_runtime_extract_options({
            'extract_flat': True, 'dump_single_json': True, 'noplaylist': True,
            'ignore_no_formats_error': True,
        }, settings, target)
        with tempfile.TemporaryDirectory(prefix='discovery-', dir=workspace) as directory:
            if instagram:
                options.update(write_pages=True, working_directory=directory)
            data, success = wrapper.extract_info(target, options, stop_check=stop_check)
            images = image_ids_from_responses(directory) if instagram else set()
        if not success or not isinstance(data, dict):
            if stop_check and stop_check():
                raise InterruptedError('Media discovery cancelled')
            raise ValueError(STR.ERR_MEDIA_DISCOVERY)
        return data, images

    def expand(info, images, depth=0):
        if stop_check and stop_check():
            raise InterruptedError('Media discovery cancelled')
        if not isinstance(info, dict):
            info = {}
        kind = info.get('_type', 'video')
        if depth < 8 and kind in ('playlist', 'multi_video'):
            for child in info.get('entries') or []:
                expand(child, images, depth + 1)
            return
        if depth < 8 and kind in ('url', 'url_transparent') and info.get('url') not in resolving:
            target = info.get('url')
            if target and urlsplit(target).scheme in ('http', 'https'):
                resolving.add(target)
                try:
                    child, child_images = extract(target)
                    expand(child, images | child_images, depth + 1)
                    return
                except ValueError:
                    log.debug('Delegated media discovery failed; retaining an unknown entry')
                finally:
                    resolving.discard(target)
        identifier = str(info.get('id') or f'unknown-{len(entries) + 1}')
        extractor = str(info.get('extractor_key') or info.get('extractor') or 'unknown').lower()
        key = f'{extractor}:{identifier}'
        base_key = key
        suffix = len(entries) + 1
        while key in seen_keys:
            key = f'{base_key}:{suffix}'
            suffix += 1
        seen_keys.add(key)
        entries.append(MediaEntry(key, info, classify_entry(info, images)))

    parent, images = extract(url)
    expand(parent, images)
    return parent, entries
