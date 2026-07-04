"""In-app YouTube login browser that uses QWebEngineView and saves cookies for yt-dlp."""
import os
import shutil
from datetime import datetime
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QLabel, QFrame)
from PyQt5.QtCore import Qt, QUrl
from PyQt5.QtGui import QFont
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEngineProfile, QWebEngineSettings
from PyQt5.QtNetwork import QNetworkCookie

from constants import (
    COOKIE_FALLBACK_EXPIRY_SEC,
    GOOGLE_ACCOUNTS_DOMAIN,
    WEBENGINE_CACHE_DIR,
    WEBENGINE_STORAGE_DIR,
    YOUTUBE_DOMAIN_FRAGMENT,
    YOUTUBE_LOGIN_URL,
    YOUTUBE_ROBOTS_PATH_FRAGMENT,
    YOUTUBE_ROBOTS_URL,
)
from utils.utils import get_user_data_path
from utils.cookie_store import get_cookie_file_path
from utils.logger import log
from gui.widgets.button_sizing import set_text_button_minimum_width
from locales.strings import STR
from resources.styles import (
    SETTINGS_FONT_FAMILY, SETTINGS_SAVE_BUTTON_STYLE,
    SETTINGS_CANCEL_BUTTON_STYLE
)


def _extract_cookie_data(cookie: QNetworkCookie) -> dict:
    """Copy QNetworkCookie data into a Python dict so values remain safe after the C++ object is released."""
    domain = cookie.domain()
    name = cookie.name().data().decode('utf-8', errors='replace')
    value = cookie.value().data().decode('utf-8', errors='replace')
    path = cookie.path() or "/"
    secure = cookie.isSecure()
    
    expiry = cookie.expirationDate()
    if expiry.isValid():
        try:
            expires = int(expiry.toSecsSinceEpoch())
        except (OverflowError, RuntimeError, TypeError) as e:
            log.debug(f"Cookie expiry conversion failed, using fallback expiry: {e}")
            expires = int(datetime.now().timestamp()) + COOKIE_FALLBACK_EXPIRY_SEC
    else:
        # Session cookies: set a one-year fallback expiry.
        expires = int(datetime.now().timestamp()) + COOKIE_FALLBACK_EXPIRY_SEC
    
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
    """Dialog for YouTube in-app login."""
    
    # Login state.
    STATE_LOGIN = 0       # Waiting for login.
    STATE_STABILIZING = 1 # Loading robots.txt for cookie stabilization.
    STATE_READY = 2       # Ready to save.
    
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
        """Set up the web engine profile."""
        profile = QWebEngineProfile.defaultProfile()
        profile.setPersistentCookiesPolicy(QWebEngineProfile.AllowPersistentCookies)
        
        data_path = get_user_data_path()
        profile.setPersistentStoragePath(os.path.join(data_path, WEBENGINE_STORAGE_DIR))
        profile.setCachePath(os.path.join(data_path, WEBENGINE_CACHE_DIR))
    
    def _setup_ui(self):
        """Set up the UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Web engine view.
        self.web_view = QWebEngineView()
        
        settings = self.web_view.settings()
        settings.setAttribute(QWebEngineSettings.LocalStorageEnabled, True)
        settings.setAttribute(QWebEngineSettings.JavascriptEnabled, True)
        
        layout.addWidget(self.web_view, 1)
        
        # Bottom button bar.
        btn_frame = QFrame()
        btn_frame.setFixedHeight(48)
        btn_frame.setStyleSheet("background-color: #F5F5F5; border-top: 1px solid #E0E0E0;")
        btn_layout = QHBoxLayout(btn_frame)
        btn_layout.setContentsMargins(10, 4, 10, 4)
        
        # Status label.
        self.status_label = QLabel(STR.MSG_LOGIN_WAITING)
        self.status_label.setFont(QFont(SETTINGS_FONT_FAMILY, 9))
        self.status_label.setStyleSheet("color: #666666; border: none;")
        btn_layout.addWidget(self.status_label)
        
        btn_layout.addStretch()
        
        # Cancel button.
        cancel_btn = QPushButton(STR.BTN_CANCEL)
        cancel_btn.setFixedHeight(32)
        set_text_button_minimum_width(cancel_btn)
        cancel_btn.setCursor(Qt.PointingHandCursor)
        cancel_btn.setStyleSheet(SETTINGS_CANCEL_BUTTON_STYLE)
        cancel_btn.setAutoDefault(False)
        cancel_btn.setDefault(False)
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        
        # Save and close button.
        self.save_btn = QPushButton(STR.BTN_SAVE_CLOSE)
        self.save_btn.setFixedHeight(32)
        set_text_button_minimum_width(self.save_btn)
        self.save_btn.setCursor(Qt.PointingHandCursor)
        self.save_btn.setStyleSheet(SETTINGS_SAVE_BUTTON_STYLE)
        self.save_btn.setAutoDefault(False)
        self.save_btn.setDefault(False)
        self.save_btn.setEnabled(False)  # Disabled until cookies are stabilized.
        self.save_btn.clicked.connect(self._save_and_close)
        btn_layout.addWidget(self.save_btn)
        
        layout.addWidget(btn_frame, 0)
    
    def _setup_cookie_capture(self):
        """Set up cookie capture."""
        profile = QWebEngineProfile.defaultProfile()
        cookie_store = profile.cookieStore()
        
        # Clear existing cookies so each flow starts from a fresh login session.
        cookie_store.deleteAllCookies()
        
        cookie_store.cookieAdded.connect(self._on_cookie_added)
        cookie_store.cookieRemoved.connect(self._on_cookie_removed)
        cookie_store.loadAllCookies()
    
    def _load_login_page(self):
        """Load the login page."""
        self.web_view.load(QUrl(YOUTUBE_LOGIN_URL))
        self.web_view.urlChanged.connect(self._on_url_changed)
    
    def _on_cookie_added(self, cookie: QNetworkCookie):
        """Copy each added cookie into Python-owned data immediately."""
        try:
            data = _extract_cookie_data(cookie)
            key = f"{data['domain']}|{data['name']}"
            self._cookies[key] = data
        except (AttributeError, KeyError, RuntimeError, TypeError, UnicodeError) as e:
            log.debug(f"Failed to cache added cookie: {e}")
    
    def _on_cookie_removed(self, cookie: QNetworkCookie):
        """Handle removed cookies."""
        try:
            domain = cookie.domain()
            name = cookie.name().data().decode('utf-8', errors='replace')
            key = f"{domain}|{name}"
            self._cookies.pop(key, None)
        except (AttributeError, RuntimeError, TypeError, UnicodeError) as e:
            log.debug(f"Failed to remove cached cookie: {e}")
    
    def _on_url_changed(self, url: QUrl):
        """Handle URL changes."""
        url_str = url.toString()
        
        if self._state == self.STATE_LOGIN:
            # Detect completed login when redirected to youtube.com.
            if YOUTUBE_DOMAIN_FRAGMENT in url_str and GOOGLE_ACCOUNTS_DOMAIN not in url_str:
                log.info(f"Login detected ({len(self._cookies)} cookies), starting cookie stabilization...")
                self._state = self.STATE_STABILIZING
                
                self.status_label.setText(STR.MSG_LOGIN_STABILIZING)
                self.status_label.setStyleSheet("color: #FF9800; font-weight: bold; border: none;")
                
                # Redirect to robots.txt instead of the YouTube home page to stabilize cookies.
                # Keeping existing cookies while loading robots.txt lets cookie rotation settle.
                self.web_view.stop()
                self.web_view.load(QUrl(YOUTUBE_ROBOTS_URL))
        
        elif self._state == self.STATE_STABILIZING:
            # robots.txt loaded, so cookie stabilization is complete.
            if YOUTUBE_ROBOTS_PATH_FRAGMENT in url_str or url_str == YOUTUBE_ROBOTS_URL:
                self.web_view.loadFinished.connect(self._on_robots_loaded)
    
    def _on_robots_loaded(self, ok):
        """Complete cookie stabilization after robots.txt finishes loading."""
        if self._state != self.STATE_STABILIZING:
            return
        
        self._state = self.STATE_READY
        self.web_view.loadFinished.disconnect(self._on_robots_loaded)
        
        yt_count = len([c for c in self._cookies.values() if YOUTUBE_DOMAIN_FRAGMENT in c['domain']])
        log.info(f"Cookie stabilization complete. Total: {len(self._cookies)}, YouTube: {yt_count}")
        
        self.status_label.setText(STR.MSG_LOGIN_SUCCESS)
        self.status_label.setStyleSheet("color: #4CAF50; font-weight: bold; border: none;")
        self.save_btn.setEnabled(True)
    
    def _save_and_close(self):
        """Save cookies in Netscape format and close."""
        # Keep only youtube.com domain cookies.
        yt_cookies = {
            k: v for k, v in self._cookies.items()
            if YOUTUBE_DOMAIN_FRAGMENT in v['domain']
        }
        
        log.info(f"Total cookies: {len(self._cookies)}, YouTube cookies: {len(yt_cookies)}")
        
        if not yt_cookies:
            log.warning("No YouTube cookies found")
            self.status_label.setText(STR.ERR_LOGIN_NO_COOKIES)
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
            
            # Remove WebEngine cache/storage directories; cookies.txt is enough.
            self._cleanup_webengine_data()
            
            self.accept()
            
        except Exception as e:
            log.error(f"Failed to save cookies: {e}", exc_info=True)
            self.status_label.setText(STR.ERR_LOGIN_SAVE_FAILED.format(error=e))
            self.status_label.setStyleSheet("color: #F44336; font-weight: bold; border: none;")
    
    def _cleanup_webengine_data(self):
        """Remove WebEngine cache and storage directories when cookies.txt is enough."""
        data_path = get_user_data_path()
        for folder in (WEBENGINE_CACHE_DIR, WEBENGINE_STORAGE_DIR):
            path = os.path.join(data_path, folder)
            if os.path.exists(path):
                try:
                    shutil.rmtree(path)
                    log.info(f"Cleaned up {folder}")
                except OSError as e:
                    log.warning(f"Failed to clean up {folder}: {e}")
    
    
    def closeEvent(self, event):
        """Clean up when the dialog closes."""
        try:
            profile = QWebEngineProfile.defaultProfile()
            cookie_store = profile.cookieStore()
            cookie_store.cookieAdded.disconnect(self._on_cookie_added)
            cookie_store.cookieRemoved.disconnect(self._on_cookie_removed)
        except (RuntimeError, TypeError) as e:
            log.debug(f"Failed to disconnect cookie signals during login browser close: {e}")
        
        try:
            self.web_view.stop()
            self.web_view.setUrl(QUrl("about:blank"))
        except RuntimeError as e:
            log.debug(f"Failed to stop login browser web view during close: {e}")
        
        super().closeEvent(event)
