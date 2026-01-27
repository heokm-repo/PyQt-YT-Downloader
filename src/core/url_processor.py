"""
URL 처리 전담 클래스
URL 검증, 정제, 플레이리스트/비디오 구분 등의 로직을 담당
"""
from typing import Optional, Tuple
from urllib.parse import urlparse, parse_qs

from PyQt5.QtWidgets import QMessageBox

from utils.utils import validate_url
from core.youtube_handler import _sanitize_url, has_video_and_list


class UrlProcessResult:
    """URL 처리 결과를 담는 데이터 클래스"""
    def __init__(self, clean_url: str, is_playlist: bool, video_id: Optional[str] = None):
        self.clean_url = clean_url
        self.is_playlist = is_playlist
        self.video_id = video_id


class UrlProcessor:
    """URL 처리 전담 클래스"""
    
    @staticmethod
    def extract_video_id(url: str) -> Optional[str]:
        """
        URL에서 video_id 추출
        
        Args:
            url: YouTube URL
            
        Returns:
            video_id 또는 None
        """
        if not url:
            return None
        
        try:
            parsed = urlparse(url)
            qs = parse_qs(parsed.query)

            # 일반 watch URL (?v=VIDEO_ID)
            if 'v' in qs:
                return qs.get('v', [None])[0]

            # youtu.be 단축 URL (https://youtu.be/VIDEO_ID)
            if parsed.netloc.endswith('youtu.be') and parsed.path:
                video_id = parsed.path.strip('/')
                return video_id or None

            return None
        except (ValueError, KeyError):
            return None
    
    @staticmethod
    def ask_user_preference(parent) -> Optional[bool]:
        """
        사용자에게 플레이리스트/비디오 선택 다이얼로그 표시
        
        Args:
            parent: 부모 위젯 (QMainWindow)
            
        Returns:
            True: 플레이리스트 선택
            False: 단일 영상 선택
            None: 취소
        """
        msg_box = QMessageBox(parent)
        msg_box.setWindowTitle('다운로드 선택')
        msg_box.setText('이 URL은 비디오와 플레이리스트 정보를 모두 포함하고 있습니다.')
        msg_box.setInformativeText('어떻게 다운로드하시겠습니까?')
        msg_box.setIcon(QMessageBox.Question)
        
        # 버튼 추가 및 텍스트 설정
        btn_playlist = msg_box.addButton('플레이리스트 전체', QMessageBox.YesRole)
        btn_video = msg_box.addButton('이 영상만', QMessageBox.NoRole)
        btn_cancel = msg_box.addButton('취소', QMessageBox.RejectRole)
        
        msg_box.setDefaultButton(btn_video)  # 기본 선택: 이 영상만
        msg_box.exec_()
        
        clicked_button = msg_box.clickedButton()
        if clicked_button == btn_cancel:
            return None
        elif clicked_button == btn_playlist:
            return True
        else:
            return False
    
    @staticmethod
    def process_url(url: str, parent) -> Optional[UrlProcessResult]:
        """
        URL을 처리하고 결과 반환
        
        Args:
            url: 입력된 URL
            parent: 부모 위젯 (사용자 다이얼로그용)
            
        Returns:
            UrlProcessResult 또는 None (취소/실패 시)
        """
        # URL 검증
        if not url or not validate_url(url):
            QMessageBox.warning(parent, "오류", "유효한 YouTube URL을 입력해주세요.")
            return None
        
        # URL에 v(영상ID)와 list(플레이리스트ID)가 함께 있는지 확인
        prefer_playlist = False  # 기본값: 단일 영상
        if has_video_and_list(url):
            user_choice = UrlProcessor.ask_user_preference(parent)
            if user_choice is None:  # 취소
                return None
            prefer_playlist = user_choice
        
        # 선택에 따라 URL 정제
        clean_url, is_playlist = _sanitize_url(url, prefer_playlist=prefer_playlist)
        
        # video_id 추출 (단일 영상인 경우)
        video_id = None
        if not is_playlist:
            video_id = UrlProcessor.extract_video_id(clean_url)
        
        return UrlProcessResult(clean_url, is_playlist, video_id)
