"""One UI task, sequential media executions, and durable per-file results."""
import hashlib
import os
from pathlib import Path

from constants import MSG_DOWNLOAD_COMPLETE, MSG_PAUSED_BY_USER
from core.download.media_discovery import MediaEntry, discover_media
from core.download.media_manifest import completed_path, load_manifest, manifest_signature, save_manifest
from core.download.output_paths import verified_download_output_path
from core.download.result import DownloadResult
from core.download.workspace_cleanup import remove_task_workspace
from core.download.workspace_state import remove_ready_marker
from locales.strings import STR
from utils.json_store import write_json_atomic


def run_media_batch(wrapper, url, settings, workspace, save_path, progress_hook,
                    metadata_hook, stop_check, is_resume, run_single):
    signature = manifest_signature(url, settings)
    previous = load_manifest(workspace, signature) if is_resume else {}
    discovery_error = None
    try:
        parent, entries = discover_media(wrapper, url, settings, workspace, stop_check)
    except (ValueError, InterruptedError) as exc:
        if not previous:
            raise
        # A later login/network failure must not hide earlier committed outputs.
        discovery_error = exc
        parent = {'title': url}
        entries = [MediaEntry(key, item, item.get('kind', 'unknown')) for key, item in previous.items()]
    items = {}
    for entry in entries:
        info = entry.info
        old = previous.get(entry.key, {})
        path = completed_path(old, save_path)
        complete = bool(path)
        items[entry.key] = {
            'id': str(info.get('id') or ''),
            'extractor': str(info.get('extractor') or info.get('extractor_key')
                             or parent.get('extractor') or 'unknown').lower(),
            'title': info.get('title', ''), 'uploader': info.get('uploader', ''),
            'kind': entry.kind,
            'state': 'skipped' if entry.kind == 'image' else 'completed' if complete else 'pending',
            'output_path': path if complete else '',
            'size': old.get('size', 0) if complete else 0,
            'mtime_ns': old.get('mtime_ns') if complete else None,
        }
    # If the remote post changes, files already saved still belong to this task.
    for key, old in previous.items():
        if key not in items and completed_path(old, save_path):
            items[key] = dict(old)
    base_meta = {
        'id': parent.get('id'), 'extractor': parent.get('extractor', 'unknown'),
        'title': parent.get('title') or url, 'uploader': parent.get('uploader', ''),
        'thumbnail': parent.get('thumbnail') or next(
            (e.info.get('thumbnail') for e in entries if e.kind == 'media' and e.info.get('thumbnail')), None),
    }

    def publish(extra=None):
        snapshot = [dict(item) for item in items.values()]
        saved = [item for item in snapshot if item['state'] == 'completed']
        meta = {**base_meta, 'media_items': snapshot,
                'output_paths': [item['output_path'] for item in saved],
                'file_size': sum(item['size'] for item in saved), **(extra or {})}
        save_manifest(workspace, signature, items)
        if metadata_hook:
            metadata_hook(meta)

    def result(paused=False):
        records = tuple(dict(item) for item in items.values())
        paths = tuple(item['output_path'] for item in records if item['state'] == 'completed')
        skipped = sum(item['state'] == 'skipped' for item in records)
        total = len(records) - skipped
        success = total > 0 and len(paths) == total
        errors = [item['error'] for item in records if item.get('error')]
        message = (MSG_PAUSED_BY_USER if paused else MSG_DOWNLOAD_COMPLETE if success else
                   '; '.join(dict.fromkeys(errors)) if errors else STR.MSG_NO_MEDIA)
        return DownloadResult(success, message, paths[0] if paths else '', paths, records)

    publish()
    if discovery_error is not None:
        outcome = result(paused=isinstance(discovery_error, InterruptedError))
        return DownloadResult(False, MSG_PAUSED_BY_USER if isinstance(discovery_error, InterruptedError)
                              else str(discovery_error), outcome.final_path, outcome.final_paths, outcome.items)
    for entry in entries:
        item = items[entry.key]
        if item['state'] in ('completed', 'skipped'):
            continue
        if stop_check and stop_check():
            return result(paused=True)
        if entry.kind == 'unknown':
            item.update(state='failed', error=STR.ERR_MEDIA_UNKNOWN)
            publish()
            continue
        token = hashlib.sha256(entry.key.encode('utf-8')).hexdigest()[:12]
        child_workspace = Path(workspace, 'entries', token)
        child_workspace.mkdir(parents=True, exist_ok=True)
        if previous.get(entry.key, {}).get('state') == 'completed':
            # A deleted/replaced completed output must really be downloaded again.
            remove_ready_marker(str(child_workspace))
        info_path = child_workspace / '.entry_info.json'
        info = dict(entry.info)
        # A resolved leaf carries its own formats/headers. Do not re-extract its
        # parent URL (which could download the entire post again).
        info['_type'] = 'video'
        write_json_atomic(info_path, info)
        child_settings = {k: v for k, v in settings.items() if not k.startswith('_')}
        template = child_settings.get('output_template', '%(title)s.%(ext)s')
        if len(entries) > 1:
            child_settings['output_template'] = template.replace('.%(ext)s', f' [{token}].%(ext)s')
            if child_settings['output_template'] == template:
                child_settings['output_template'] = f'%(title)s [{token}].%(ext)s'
        child_settings['_media_info_filename'] = str(info_path)
        child_settings['_media_workspace'] = str(child_workspace)
        item['state'] = 'downloading'

        def metadata(info):
            # Stream estimates are transient, not a journal checkpoint. Each
            # committed result below still gets an atomic save before UI delivery.
            if metadata_hook:
                metadata_hook({'media_progress_reset': True, **{
                    k: info[k] for k in ('download_streams', 'video_size', 'audio_size') if k in info
                }})

        try:
            child = run_single(url, child_settings, progress_hook, is_resume=is_resume,
                               stop_check=stop_check, metadata_hook=metadata)
        except InterruptedError:
            child = DownloadResult(False, MSG_PAUSED_BY_USER)
        except Exception as exc:
            child = DownloadResult(False, str(exc))
        finally:
            info_path.unlink(missing_ok=True)
        if child.success:
            path = verified_download_output_path(child.final_path, save_path)
            if not path:
                item.update(state='failed', error=STR.ERR_OUTPUT_PATH_VERIFY)
            else:
                stat = os.stat(path)
                item.update(state='completed', output_path=path, size=stat.st_size, mtime_ns=stat.st_mtime_ns)
        else:
            item.update(state='failed', error=child.message)
        publish()
        if not child.success and MSG_PAUSED_BY_USER in child.message:
            return result(paused=True)
    outcome = result()
    if outcome.success:
        remove_task_workspace(workspace)
    return outcome
