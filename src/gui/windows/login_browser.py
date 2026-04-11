"""
인앱 YouTube 로그인 브라우저
QWebEngineView를 사용하여 Google 로그인을 처리하고 쿠키를 추출합니다.

중요: yt-dlp가 쿠키를 올바르게 사용하려면, 로그인 후 youtube.com/robots.txt에
먼저 접속하여 쿠키 회전(rotation)을 방지해야 합니다.
"""
import os
import shutil
from datetime import datetime
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QLabel, QFrame)
from PyQt5.QtCore import Qt, QUrl
from PyQt5.QtGui import QFont
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEngineProfile, QWebEngineSettings
from PyQt5.QtNetwork import QNetworkCookie

from utils.utils import get_user_data_path
from utils.logger import log
from locales.strings import STR
from resources.styles import (
    SETTINGS_FONT_FAMILY, SETTINGS_SAVE_BUTTON_STYLE,
    SETTINGS_CANCEL_BUTTON_STYLE
)

# YouTube 로그인 URL
YOUTUBE_LOGIN_URL = "https://accounts.google.com/ServiceLogin?service=youtube&uilel=3&passive=true&continue=https%3A%2F%2Fwww.youtube.com%2Fsignin"

# 쿠키 안정화를 위한 URL (yt-dlp 공식 권장)
YOUTUBE_ROBOTS_URL = "https://www.youtube.com/robots.txt"

# 쿠키 파일 이름
COOKIE_FILENAME = "cookies.txt"


def get_cookie_file_path():
    """쿠키 파일 경로를 반환합니다."""
    return os.path.join(get_user_data_path(), COOKIE_FILENAME)


def cookie_file_exists():
    """쿠키 파일이 존재하는지 확인합니다."""
    return os.path.exists(get_cookie_file_path())


def _extract_cookie_data(cookie: QNetworkCookie) -> dict:
    """
    QNetworkCookie에서 Python dict로 데이터 추출 (즉시 복사).
    C++ 객체가 나중에 해제되어도 안전하도록 모든 값을 문자열로 변환.
    """
    domain = cookie.domain()
    name = cookie.name().data().decode('utf-8', errors='replace')
    value = cookie.value().data().decode('utf-8', errors='replace')
    path = cookie.path() or "/"
    secure = cookie.isSecure()
    
    expiry = cookie.expirationDate()
    if expiry.isValid():
        try:
            expires = int(expiry.toSecsSinceEpoch())
        except Exception:
            expires = int(datetime.now().timestamp()) + 365 * 24 * 3600
    else:
        # 세션 쿠키: 1년 후 만료로 설정
        expires = int(datetime.now().timestamp()) + 365 * 24 * 3600
    
    return {
        'domain': domain,
        'include_subdomains': domain.startswith('.'),
        'path': path,
        'secure': secure,
        'expires': expires,
        'name': name,
        'value': value,
    }


class LoginBrowser(QDialog):
    """YouTube 인앱 로그인 브라우저 다이얼로그"""
    
    # 로그인 상태
    STATE_LOGIN = 0       # 로그인 대기 중
    STATE_STABILIZING = 1 # robots.txt 로드 중 (쿠키 안정화)
    STATE_READY = 2       # 저장 가능
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(STR.TITLE_LOGIN_BROWSER)
        self.resize(500, 700)
        self.setWindowFlags(Qt.Window | Qt.WindowCloseButtonHint)
        
        self._state = self.STATE_LOGIN
        self._cookies = {}  # "domain|name" -> dict
        self._setup_profile()
        self._setup_ui()
        self._setup_cookie_capture()
        self._load_login_page()
    
    def _setup_profile(self):
        """웹 엔진 프로필 설정"""
        profile = QWebEngineProfile.defaultProfile()
        profile.setPersistentCookiesPolicy(QWebEngineProfile.AllowPersistentCookies)
        
        data_path = get_user_data_path()
        profile.setPersistentStoragePath(os.path.join(data_path, "webengine_storage"))
        profile.setCachePath(os.path.join(data_path, "webengine_cache"))
    
    def _setup_ui(self):
        """UI 구성"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # 웹 엔진 뷰
        self.web_view = QWebEngineView()
        
        settings = self.web_view.settings()
        settings.setAttribute(QWebEngineSettings.LocalStorageEnabled, True)
        settings.setAttribute(QWebEngineSettings.JavascriptEnabled, True)
        
        layout.addWidget(self.web_view, 1)
        
        # 하단 버튼 바
        btn_frame = QFrame()
        btn_frame.setFixedHeight(48)
        btn_frame.setStyleSheet("background-color: #F5F5F5; border-top: 1px solid #E0E0E0;")
        btn_layout = QHBoxLayout(btn_frame)
        btn_layout.setContentsMargins(10, 4, 10, 4)
        
        # 상태 라벨
        self.status_label = QLabel(STR.MSG_LOGIN_WAITING)
        self.status_label.setFont(QFont(SETTINGS_FONT_FAMILY, 9))
        self.status_label.setStyleSheet("color: #666666; border: none;")
        btn_layout.addWidget(self.status_label)
        
        btn_layout.addStretch()
        
        # 취소 버튼
        cancel_btn = QPushButton(STR.BTN_CANCEL)
        cancel_btn.setFixedSize(80, 32)
        cancel_btn.setCursor(Qt.PointingHandCursor)
        cancel_btn.setStyleSheet(SETTINGS_CANCEL_BUTTON_STYLE)
        cancel_btn.setAutoDefault(False)
        cancel_btn.setDefault(False)
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        
        # 저장 및 닫기 버튼
        self.save_btn = QPushButton(STR.BTN_SAVE_CLOSE)
        self.save_btn.setFixedSize(120, 32)
        self.save_btn.setCursor(Qt.PointingHandCursor)
        self.save_btn.setStyleSheet(SETTINGS_SAVE_BUTTON_STYLE)
        self.save_btn.setAutoDefault(False)
        self.save_btn.setDefault(False)
        self.save_btn.setEnabled(False)  # 쿠키 안정화 전까지 비활성화
        self.save_btn.clicked.connect(self._save_and_close)
        btn_layout.addWidget(self.save_btn)
        
        layout.addWidget(btn_frame, 0)
    
    def _setup_cookie_capture(self):
        """쿠키 캡처 설정"""
        profile = QWebEngineProfile.defaultProfile()
        cookie_store = profile.cookieStore()
        
        # 기존 쿠키 삭제 (항상 새 로그인 세션으로 시작)
        cookie_store.deleteAllCookies()
        
        cookie_store.cookieAdded.connect(self._on_cookie_added)
        cookie_store.cookieRemoved.connect(self._on_cookie_removed)
        cookie_store.loadAllCookies()
    
    def _load_login_page(self):
        """로그인 페이지 로드"""
        self.web_view.load(QUrl(YOUTUBE_LOGIN_URL))
        self.web_view.urlChanged.connect(self._on_url_changed)
    
    def _on_cookie_added(self, cookie: QNetworkCookie):
        """쿠키가 추가될 때 즉시 Python dict 로 복사하여 저장"""
        try:
            data = _extract_cookie_data(cookie)
            key = f"{data['domain']}|{data['name']}"
            self._cookies[key] = data
        except Exception:
            pass
    
    def _on_cookie_removed(self, cookie: QNetworkCookie):
        """쿠키가 제거될 때 호출"""
        try:
            domain = cookie.domain()
            name = cookie.name().data().decode('utf-8', errors='replace')
            key = f"{domain}|{name}"
            self._cookies.pop(key, None)
        except Exception:
            pass
    
    def _on_url_changed(self, url: QUrl):
        """URL 변경 감지"""
        url_str = url.toString()
        
        if self._state == self.STATE_LOGIN:
            # 로그인 완료 감지: youtube.com으로 리다이렉트됨
            if 'youtube.com' in url_str and 'accounts.google.com' not in url_str:
                log.info(f"Login detected ({len(self._cookies)} cookies), starting cookie stabilization...")
                self._state = self.STATE_STABILIZING
                
                self.status_label.setText("Stabilizing cookies...")
                self.status_label.setStyleSheet("color: #FF9800; font-weight: bold; border: none;")
                
                # YouTube 메인 페이지 대신 robots.txt로 리다이렉트 (쿠키 안정화)
                # 기존 쿠키를 유지한 채 robots.txt에 접속하면 쿠키 회전이 완료되어 안정화됨
                self.web_view.stop()
                self.web_view.load(QUrl(YOUTUBE_ROBOTS_URL))
        
        elif self._state == self.STATE_STABILIZING:
            # robots.txt 로드 완료 → 쿠키 안정화 완료
            if 'robots.txt' in url_str or url_str == YOUTUBE_ROBOTS_URL:
                self.web_view.loadFinished.connect(self._on_robots_loaded)
    
    def _on_robots_loaded(self, ok):
        """robots.txt 로드 완료 후 쿠키 안정화 완료"""
        if self._state != self.STATE_STABILIZING:
            return
        
        self._state = self.STATE_READY
        self.web_view.loadFinished.disconnect(self._on_robots_loaded)
        
        yt_count = len([c for c in self._cookies.values() if 'youtube.com' in c['domain']])
        log.info(f"Cookie stabilization complete. Total: {len(self._cookies)}, YouTube: {yt_count}")
        
        self.status_label.setText(STR.MSG_LOGIN_SUCCESS)
        self.status_label.setStyleSheet("color: #4CAF50; font-weight: bold; border: none;")
        self.save_btn.setEnabled(True)
    
    def _save_and_close(self):
        """쿠키를 Netscape 형식으로 저장하고 닫기"""
        # youtube.com 도메인 쿠키만 필터링
        yt_cookies = {
            k: v for k, v in self._cookies.items()
            if 'youtube.com' in v['domain']
        }
        
        log.info(f"Total cookies: {len(self._cookies)}, YouTube cookies: {len(yt_cookies)}")
        
        if not yt_cookies:
            log.warning("No YouTube cookies found")
            self.status_label.setText("No YouTube cookies captured!")
            self.status_label.setStyleSheet("color: #F44336; font-weight: bold; border: none;")
            return
        
        try:
            cookie_path = get_cookie_file_path()
            os.makedirs(os.path.dirname(cookie_path), exist_ok=True)
            
            saved_count = 0
            with open(cookie_path, 'w', encoding='utf-8') as f:
                f.write("# Netscape HTTP Cookie File\n")
                f.write(f"# Generated by YT Downloader at {datetime.now().isoformat()}\n")
                f.write("# This file is auto-generated. Do not edit.\n\n")
                
                for data in yt_cookies.values():
                    domain = data['domain']
                    flag = "TRUE" if data['include_subdomains'] else "FALSE"
                    path = data['path']
                    secure = "TRUE" if data['secure'] else "FALSE"
                    expires = str(data['expires'])
                    name = data['name']
                    value = data['value']
                    
                    f.write(f"{domain}\t{flag}\t{path}\t{secure}\t{expires}\t{name}\t{value}\n")
                    saved_count += 1
            
            log.info(f"Cookies saved to: {cookie_path} ({saved_count} cookies)")
            
            # webengine 캐시/스토리지 폴더 삭제 (cookies.txt만 있으면 됨)
            self._cleanup_webengine_data()
            
            self.accept()
            
        except Exception as e:
            log.error(f"Failed to save cookies: {e}", exc_info=True)
            self.status_label.setText(f"Save failed: {e}")
            self.status_label.setStyleSheet("color: #F44336; font-weight: bold; border: none;")
    
    def _cleanup_webengine_data(self):
        """webengine 캐시/스토리지 폴더 삭제 (cookies.txt만 있으면 충분)"""
        data_path = get_user_data_path()
        for folder in ('webengine_cache', 'webengine_storage'):
            path = os.path.join(data_path, folder)
            if os.path.exists(path):
                try:
                    shutil.rmtree(path)
                    log.info(f"Cleaned up {folder}")
                except Exception as e:
                    log.warning(f"Failed to clean up {folder}: {e}")
    
    
    def closeEvent(self, event):
        """다이얼로그 닫기 시 정리"""
        try:
            profile = QWebEngineProfile.defaultProfile()
            cookie_store = profile.cookieStore()
            cookie_store.cookieAdded.disconnect(self._on_cookie_added)
            cookie_store.cookieRemoved.disconnect(self._on_cookie_removed)
        except Exception:
            pass
        
        try:
            self.web_view.stop()
            self.web_view.setUrl(QUrl("about:blank"))
        except Exception:
            pass
        
        super().closeEvent(event)
