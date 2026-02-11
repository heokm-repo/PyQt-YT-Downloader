"""
URL 처리 전담 클래스
URL 검증, 정제, 플레이리스트/비디오 구분 등의 로직을 담당
"""
from typing import Optional, Tuple
from urllib.parse import urlparse, parse_qs



from utils.utils import validate_url
from core.youtube_handler import _sanitize_url, has_video_and_list
import constants


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
            if parsed.netloc.endswith(constants.DOMAIN_YOUTU_BE) and parsed.path:
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
            True: 플레이리스트 선택 (1)
            False: 단일 영상 선택 (2)
            None: 취소 (0)
        """
        from gui.widgets.message_dialog import MessageDialog
        from locales.strings import STR
        
        # 버튼 순서: [0: 플레이리스트, 1: 단일 영상, 2: 취소]
        # MessageDialog의 custom_buttons 인덱스와 매핑됨
        buttons = [
            {'text': STR.BTN_CHOICE_ALL, 'role': 'action'},
            {'text': STR.BTN_CHOICE_VIDEO, 'role': 'action'},
            {'text': STR.BTN_CANCEL, 'role': 'reject'}
        ]
        
        dialog = MessageDialog(STR.TITLE_CHOICE, 
                               STR.MSG_CHOICE,
                               MessageDialog.QUESTION, parent, buttons=buttons)
                               
        dialog.exec_()
        
        # clicked_button_index는 누른 버튼의 리스트 내 인덱스
        # 0: 플레이리스트, 1: 단일 영상, 그 외: 취소/닫기
        if dialog.clicked_button_index == 0:
            return True
        elif dialog.clicked_button_index == 1:
            return False
        else: # Cancel or closed
            return None
    
    @staticmethod
    def process_url(url: str, parent) -> Optional['UrlProcessResult']:
        """
        URL을 처리하고 결과 반환
        
        Args:
            url: 입력된 URL
            parent: 부모 위젯 (사용자 다이얼로그용)
            
        Returns:
            UrlProcessResult 또는 None (취소/실패 시)
        """
        from locales.strings import STR
        if not url or not validate_url(url):
            from gui.widgets.message_dialog import MessageDialog
            MessageDialog(STR.TITLE_ERROR, STR.ERR_INVALID_URL, 
                          MessageDialog.WARNING, parent).exec_()
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
