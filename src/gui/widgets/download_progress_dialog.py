"""
초기 바이너리 다운로드 진행 다이얼로그
- 첫 실행 시 yt-dlp와 ffmpeg 다운로드 진행률 표시
- 모달 다이얼로그 (취소 불가)
"""
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QProgressBar,
                             QPushButton, QFrame, QGraphicsDropShadowEffect)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont, QColor
from constants import change_language
from locales.strings import STR
from resources.styles import (
    SETTINGS_CONTAINER_STYLE, SETTINGS_TITLE_LABEL_STYLE,
    SETTINGS_LABEL_STYLE, PROGRESS_BAR_STYLE,
    # Moved Constants
    SETTINGS_SHADOW_BLUR_RADIUS, SETTINGS_SHADOW_ALPHA,
    SETTINGS_FONT_FAMILY,
    # New Constants
    DOWNLOAD_DIALOG_WIDTH, DOWNLOAD_DIALOG_HEIGHT,
    DETAIL_LABEL_STYLE, INFO_LABEL_STYLE
)
from utils.logger import log


class DownloadWorker(QThread):
    """백그라운드에서 바이너리 다운로드 수행"""
    
    progress = pyqtSignal(str, int, int)  # binary_name, downloaded, total
    finished = pyqtSignal(bool)  # success
    status = pyqtSignal(str)  # status message
    
    def __init__(self, update_mode=False, updates=None):
        super().__init__()
        self.update_mode = update_mode
        self.updates = updates  # 업데이트할 바이너리 목록
        self.is_cancelled = False
    
    def cancel(self):
        """다운로드 취소 요청"""
        self.is_cancelled = True
        
    def check_cancel(self):
        """취소 여부 확인 콜백"""
        return self.is_cancelled
    
    def run(self):
        """다운로드 실행"""
        try:
            if self.update_mode:
                from utils.bin_manager import update_binaries
                
                def progress_callback(binary_name, downloaded, total):
                    self.progress.emit(binary_name, downloaded, total)
                
                # updates를 전달하여 해당 바이너리만 업데이트
                results = update_binaries(progress_callback, self.updates, self.check_cancel)
                
                if self.is_cancelled:
                    self.finished.emit(False)
                    return

                success = all(results.values())
                self.finished.emit(success)
            else:
                from utils.bin_manager import download_initial_binaries
                
                def progress_callback(binary_name, downloaded, total):
                    self.progress.emit(binary_name, downloaded, total)
                
                success = download_initial_binaries(progress_callback, self.check_cancel)
                
                if self.is_cancelled:
                    self.finished.emit(False)
                    return
                    
                self.finished.emit(success)
            
        except Exception as e:
            log.error(f"Download worker error: {e}")
            self.finished.emit(False)


class DownloadProgressDialog(QDialog):
    """초기 바이너리 다운로드 진행 다이얼로그"""
    
    def __init__(self, parent=None, update_mode=False, updates=None):
        super().__init__(parent)
        
        self.update_mode = update_mode
        self.updates = updates  # 업데이트할 바이너리 목록
        title_text = STR.TITLE_APP_UPDATE if update_mode else STR.TITLE_INIT
        
        self.setWindowTitle(title_text)
        # If SETTINGS_DIALOG_WIDTH is 500-600, it's fine.
        # Let's use a slightly smaller fixed size for this specific dialog as it has less content,
        # or use the literal 450 but make sure styles match.
        self.setFixedSize(DOWNLOAD_DIALOG_WIDTH, DOWNLOAD_DIALOG_HEIGHT) 
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        self._setup_ui()
        
        # 다운로드 워커
        self.worker = None
        self.download_success = False
    
    def _setup_ui(self):
        """UI 구성"""
        # 메인 레이아웃 (투명 배경 위)
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # 실제 컨텐츠가 담길 컨테이너
        container = QFrame()
        container.setObjectName("Container")
        container.setStyleSheet(SETTINGS_CONTAINER_STYLE)
        
        # 그림자 효과
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(SETTINGS_SHADOW_BLUR_RADIUS)
        shadow.setColor(QColor(0, 0, 0, SETTINGS_SHADOW_ALPHA))
        shadow.setOffset(0, 0)
        container.setGraphicsEffect(shadow)
        
        main_layout.addWidget(container)
        
        # 컨테이너 내부 레이아웃
        layout = QVBoxLayout(container)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)
        
        # 제목
        title = QLabel(STR.TITLE_INIT if not self.update_mode else STR.TITLE_APP_UPDATE)
        title.setFont(QFont(SETTINGS_FONT_FAMILY, 14, QFont.Bold))
        title.setStyleSheet(SETTINGS_TITLE_LABEL_STYLE)
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # 상태 메시지
        self.status_label = QLabel(STR.MSG_INIT_DESC)
        self.status_label.setFont(QFont(SETTINGS_FONT_FAMILY, 10))
        self.status_label.setStyleSheet(SETTINGS_LABEL_STYLE)
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setWordWrap(True)
        layout.addWidget(self.status_label)
        
        # 진행률 바
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setAlignment(Qt.AlignCenter)
        self.progress_bar.setFixedHeight(25)
        # Use centralized style, possibly overriding font size if needed
        self.progress_bar.setStyleSheet(PROGRESS_BAR_STYLE)
        layout.addWidget(self.progress_bar)
        
        # 상세 정보
        self.detail_label = QLabel(STR.MSG_INIT_PREPARING)
        self.detail_label.setFont(QFont(SETTINGS_FONT_FAMILY, 9))
        self.detail_label.setStyleSheet(DETAIL_LABEL_STYLE)
        self.detail_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.detail_label)
        
        # 안내 메시지
        info_text = STR.MSG_UPDATE_DL if self.update_mode else STR.MSG_INIT_INFO
        info_label = QLabel(info_text)
        info_label.setFont(QFont(SETTINGS_FONT_FAMILY, 8))
        # Use a consistent color or define a new constant if reused often
        info_label.setStyleSheet(INFO_LABEL_STYLE)
        info_label.setAlignment(Qt.AlignCenter)
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        
        # 버튼 레이아웃 (취소 버튼)
        btn_layout = QHBoxLayout()
        btn_layout.setContentsMargins(0, 10, 0, 0)
        btn_layout.addStretch()
        
        self.cancel_btn = QPushButton(STR.BTN_CANCEL)
        self.cancel_btn.setCursor(Qt.PointingHandCursor)
        self.cancel_btn.setFixedHeight(30)
        self.cancel_btn.setFixedWidth(100)
        # Use existing style constants, e.g., SETTINGS_CANCEL_BUTTON_STYLE
        from resources.styles import SETTINGS_CANCEL_BUTTON_STYLE
        self.cancel_btn.setStyleSheet(SETTINGS_CANCEL_BUTTON_STYLE)
        self.cancel_btn.clicked.connect(self.cancel_download)
        
        btn_layout.addWidget(self.cancel_btn)
        btn_layout.addStretch()
        
        layout.addLayout(btn_layout)
        
        layout.addStretch()
    
    def cancel_download(self):
        """다운로드 취소"""
        if self.worker and self.worker.isRunning():
            self.status_label.setText(STR.MSG_INIT_FAILED) # Or a specific "Cancelling..." message
            self.detail_label.setText("Cancelling...")
            self.cancel_btn.setEnabled(False) # Prevent multiple clicks
            self.worker.cancel()
            # Worker will finish shortly with success=False
            # The _on_finished will be called
        else:
            self.reject()

    def start_download(self):
        """다운로드 시작"""
        if self.worker is not None:
            return
        
        self.worker = DownloadWorker(self.update_mode, self.updates)
        self.worker.progress.connect(self._on_progress)
        self.worker.finished.connect(self._on_finished)
        self.worker.start()
        
        mode_text = "update" if self.update_mode else "initial download"
        log.info(f"Started binary {mode_text}")
    
    def _on_progress(self, binary_name: str, downloaded: int, total: int):
        """
        진행률 업데이트
        
        Args:
            binary_name: 'yt-dlp' 또는 'ffmpeg'
            downloaded: 다운로드한 바이트
            total: 전체 바이트
        """
        if total > 0:
            percent = int((downloaded / total) * 100)
            self.progress_bar.setValue(percent)
            
            # MB 단위로 변환
            downloaded_mb = downloaded / (1024 * 1024)
            total_mb = total / (1024 * 1024)
            
            # 상태 업데이트
            display_name = "yt-dlp" if binary_name == "yt-dlp" else "FFmpeg"
            self.status_label.setText(STR.MSG_INIT_DL_STATUS.format(item=display_name))
            self.detail_label.setText(f"{downloaded_mb:.1f} MB / {total_mb:.1f} MB ({percent}%)")
    
    def _on_finished(self, success: bool):
        """
        다운로드 완료
        
        Args:
            success: 성공 여부
        """
        self.download_success = success
        
        if success:
            self.progress_bar.setValue(100)
            self.status_label.setText(STR.MSG_INIT_COMPLETE)
            self.detail_label.setText(STR.MSG_INIT_STARTING)
            self.cancel_btn.setEnabled(False) 
            self.cancel_btn.setVisible(False)
            log.info("Initial binary download completed successfully")
            
            # 잠시 후 닫기 (성공 시에만 자동 닫기)
            from PyQt5.QtCore import QTimer
            QTimer.singleShot(1000, self.accept)
            
        elif self.worker and self.worker.is_cancelled:
            self.download_success = False
            self.status_label.setText(STR.MSG_INIT_FAILED)
            self.detail_label.setText("Download Cancelled")
            log.info("Download cancelled by user")
            self.reject() # Immediately close on cancel failure
            
        else:
            self.status_label.setText(STR.MSG_INIT_FAILED)
            self.detail_label.setText(STR.ERR_INIT_DOWNLOAD)
            self.cancel_btn.setText(STR.BTN_CLOSE) # Change Cancel to Close
            self.cancel_btn.setEnabled(True)
            # Re-connect to reject to ensure it closes
            try:
                self.cancel_btn.clicked.disconnect()
            except:
                pass
            self.cancel_btn.clicked.connect(self.reject)
            
            log.error("Initial binary download failed")
            # 실패 시 자동 닫기 제거, 유저가 확인하고 닫도록 함

    
    def exec_(self):
        """다이얼로그 실행 (자동으로 다운로드 시작)"""
        self.start_download()
        return super().exec_()
