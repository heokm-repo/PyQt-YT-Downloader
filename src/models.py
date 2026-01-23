"""
데이터 모델 정의
DownloadTask 등 핵심 데이터 구조를 dataclass로 관리
"""
from dataclasses import dataclass, field
from typing import Dict, Any, Optional

from constants import TaskStatus


@dataclass
class DownloadTask:
    """다운로드 작업을 나타내는 데이터 클래스"""
    id: int
    url: str
    status: TaskStatus = TaskStatus.WAITING
    video_id: Optional[str] = None
    output_path: str = ""
    settings: Dict[str, Any] = field(default_factory=dict)
    meta: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """JSON 직렬화용 딕셔너리 변환"""
        return {
            'id': self.id,
            'url': self.url,
            'status': self.status.value,
            'video_id': self.video_id,
            'output_path': self.output_path,
            'settings': self.settings,
            'meta': self.meta
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DownloadTask':
        """딕셔너리에서 DownloadTask 객체 생성 (JSON 역직렬화용)"""
        return cls(
            id=data.get('id', 0),
            url=data.get('url', ''),
            status=TaskStatus.from_string(data.get('status', TaskStatus.WAITING.value)),
            video_id=data.get('video_id'),
            output_path=data.get('output_path', ''),
            settings=data.get('settings', {}),
            meta=data.get('meta', {})
        )
    
    def is_active(self) -> bool:
        """작업이 진행 중인 상태인지 확인"""
        return self.status in [TaskStatus.WAITING, TaskStatus.DOWNLOADING, TaskStatus.PAUSED]
    
    def is_completed(self) -> bool:
        """작업이 완료된 상태인지 확인"""
        return self.status == TaskStatus.FINISHED
    
    def is_failed(self) -> bool:
        """작업이 실패한 상태인지 확인"""
        return self.status == TaskStatus.FAILED
