"""Helpers for applying fetched metadata to download tasks."""

from typing import Any, MutableMapping, Protocol


class MetadataTask(Protocol):
    video_id: str | None
    extractor: str
    meta: MutableMapping[str, Any]


def apply_metadata_to_task(task: MetadataTask, metadata: MutableMapping[str, Any]) -> None:
    task.meta = metadata

    video_id = metadata.get("id")
    extractor = metadata.get("extractor", "unknown")
    if extractor:
        extractor = extractor.lower()

    if not task.video_id and video_id:
        task.video_id = video_id

    if extractor and (task.extractor == "unknown" or not task.extractor):
        task.extractor = extractor
