"""Validate persisted task records before restoring GUI objects."""

from utils.logger import log


def valid_task_records(items):
    """Keep valid records in order, excluding malformed or duplicate IDs."""
    if not isinstance(items, (list, tuple)):
        log.warning("Ignoring task list with invalid root type")
        return []
    records = []
    seen = set()
    for item in items:
        if not isinstance(item, dict):
            log.warning("Ignoring invalid task record")
            continue
        task_id = item.get("id", 0)
        if type(task_id) is not int or task_id < 0 or task_id in seen:
            log.warning("Ignoring task record with invalid or duplicate ID")
            continue
        if any(not isinstance(item.get(key, ""), str)
               for key in ("url", "status", "extractor", "output_path")):
            log.warning("Ignoring task record with invalid text fields")
            continue
        if any(not isinstance(item.get(key, {}), dict) for key in ("settings", "meta")):
            log.warning("Ignoring task record with invalid settings or metadata")
            continue
        seen.add(task_id)
        records.append(item)
    return records
