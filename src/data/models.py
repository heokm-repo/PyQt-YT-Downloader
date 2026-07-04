"""Data models for core dataclass structures such as DownloadTask."""
from dataclasses import dataclass, field
from typing import Dict, Any, Optional

from constants import TaskStatus


@dataclass
class DownloadTask:
    """Data class representing a download task."""
    id: int
    url: str
    status: TaskStatus = TaskStatus.WAITING
    video_id: Optional[str] = None
    extractor: str = 'unknown'
    output_path: str = ""
    settings: Dict[str, Any] = field(default_factory=dict)
    meta: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to a JSON-serializable dictionary."""
        return {
            'id': self.id,
            'url': self.url,
            'status': self.status.value,
            'video_id': self.video_id,
            'extractor': self.extractor,
            'output_path': self.output_path,
            'settings': self.settings,
            'meta': self.meta
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DownloadTask':
        """Create a DownloadTask from a dictionary during JSON deserialization."""
        return cls(
            id=data.get('id', 0),
            url=data.get('url', ''),
            status=TaskStatus.from_string(data.get('status', TaskStatus.WAITING.value)),
            video_id=data.get('video_id'),
            extractor=data.get('extractor', 'youtube'),  # Backward compatibility: existing data is youtube.
            output_path=data.get('output_path', ''),
            settings=data.get('settings', {}),
            meta=data.get('meta', {})
        )
    
    def is_active(self) -> bool:
        """Return whether the task is active."""
        return self.status in [TaskStatus.WAITING, TaskStatus.DOWNLOADING, TaskStatus.PAUSED]
    
    def is_completed(self) -> bool:
        """Return whether the task is completed."""
        return self.status == TaskStatus.FINISHED
    
    def is_failed(self) -> bool:
        """Return whether the task failed."""
        return self.status == TaskStatus.FAILED
