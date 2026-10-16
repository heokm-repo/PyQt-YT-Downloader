import json
from pathlib import Path
from unittest.mock import Mock

import pytest

from core.download.media_discovery import classify_entry, discover_media
from core.ytdlp.command import build_command
from core.ytdlp.info_command import build_extract_info_command


@pytest.mark.parametrize('info,expected', [
    ({'formats': []}, 'unknown'),
    ({'id': 'photo', 'formats': []}, 'unknown'),
    ({'_type': 'image'}, 'image'),
    ({'formats': [{'url': 'https://cdn/video'}]}, 'media'),
    ({'url': 'https://cdn/video', 'ext': 'mp4'}, 'media'),
    ({'url': 'https://cdn/photo.jpg'}, 'unknown'),
])
def test_only_confirmed_images_are_skipped(info, expected):
    assert classify_entry(info) == expected


def test_instagram_matches_explicit_types_and_removes_raw_responses(tmp_path):
    wrapper = Mock()
    directories = []

    def extract(url, options, **kwargs):
        directory = Path(options['working_directory'])
        directories.append(directory)
        (directory / 'response.dump').write_text(json.dumps({'items': [
            {'code': 'photo', 'media_type': 1}, {'code': 'video', 'media_type': 2},
            {'code': 'unrelated', 'media_type': 1},
        ]}), encoding='utf-8')
        return {'_type': 'playlist', 'entries': [
            {'id': 'photo', 'formats': []}, {'id': 'video', 'formats': [{'url': 'video'}]},
            {'id': 'broken', 'formats': []},
        ]}, True

    wrapper.extract_info.side_effect = extract
    _, entries = discover_media(wrapper, 'https://www.instagram.com/p/post/', {}, tmp_path)
    assert [e.kind for e in entries] == ['image', 'media', 'unknown']
    assert all(not p.exists() for p in directories)


def test_nested_delegation_and_failed_entries_remain_visible(tmp_path):
    wrapper = Mock()
    wrapper.extract_info.side_effect = [
        ({'_type': 'multi_video', 'entries': [None, {'_type': 'url', 'url': 'https://example.org/child'}]}, True),
        ({'_type': 'playlist', 'entries': [{'id': 'a', 'formats': [{'url': 'a'}]}]}, True),
    ]
    _, entries = discover_media(wrapper, 'https://example.org/post', {}, tmp_path)
    assert [e.kind for e in entries] == ['unknown', 'media']
    assert wrapper.extract_info.call_count == 2


def test_discovery_cancel_never_starts_extractor(tmp_path):
    wrapper = Mock()
    with pytest.raises(InterruptedError):
        discover_media(wrapper, 'https://example.org', {}, tmp_path, lambda: True)
    wrapper.extract_info.assert_not_called()


def test_repeated_ids_cannot_collide_with_an_existing_suffixed_id(tmp_path):
    wrapper = Mock()
    wrapper.extract_info.return_value = ({'_type': 'playlist', 'entries': [
        {'id': name, 'formats': [{'url': 'video'}]} for name in ('same', 'same:3', 'same')
    ]}, True)
    _, entries = discover_media(wrapper, 'https://example.org/post', {}, tmp_path)
    assert len(entries) == len({entry.key for entry in entries}) == 3
    assert entries[-1].key == 'unknown:same:4'


def test_discovery_flags_never_relax_actual_download_errors():
    options = {'ignore_no_formats_error': True, 'write_pages': True, 'load_info_filename': 'entry.json'}
    discovery = build_extract_info_command('engine', 'https://example.org', options)
    download = build_command('engine', None, 'https://example.org', options)
    assert '--ignore-no-formats-error' in discovery and '--write-pages' in discovery
    assert '--ignore-no-formats-error' not in download and '--ignore-errors' not in download
    assert download[-2:] == ['--load-info-json', 'entry.json']
    assert 'https://example.org' not in download
