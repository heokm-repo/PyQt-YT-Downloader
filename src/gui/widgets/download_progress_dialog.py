"""
초기 바이너리 다운로드 진행 다이얼로그
- 첫 실행 시 yt-dlp와 ffmpeg 다운로드 진행률 표시
- 모달 다이얼로그 (취소 불가)
"""
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QLabel, QProgressBar,
                             QFrame, QGraphicsDropShadowEffect)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont, QColor
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
    
    def run(self):
        """다운로드 실행"""
        try:
            if self.update_mode:
                from utils.bin_manager import update_binaries
                
                def progress_callback(binary_name, downloaded, total):
                    self.progress.emit(binary_name, downloaded, total)
                
                # updates를 전달하여 해당 바이너리만 업데이트
                results = update_binaries(progress_callback, self.updates)
                success = all(results.values())
                self.finished.emit(success)
            else:
                from utils.bin_manager import download_initial_binaries
                
                def progress_callback(binary_name, downloaded, total):
                    self.progress.emit(binary_name, downloaded, total)
                
                success = download_initial_binaries(progress_callback)
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
        title_text = "YT Downloader 업데이트" if update_mode else "YT Downloader 초기화"
        
        self.setWindowTitle(title_text)
        self.setFixedSize(450, 250)
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        self._setup_ui()
        
        # 다운로드 워커
        self.worker = None
        self.download_success = False
    
    def _setup_ui(self):
        """UI 구성"""
        # 메인 레이아웃
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # 컨테이너 프레임
        container = QFrame()
        container.setObjectName("container")
        container.setStyleSheet("""
            QFrame#container {
                background-color: #1e1e1e;
                border-radius: 10px;
                border: 1px solid #333333;
            }
        """)
        
        # 그림자 효과
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 100))
        shadow.setOffset(0, 4)
        container.setGraphicsEffect(shadow)
        
        main_layout.addWidget(container)
        
        # 컨테이너 내부 레이아웃
        layout = QVBoxLayout(container)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)
        
        # 제목
        title = QLabel("YT Downloader 초기화 중...")
        title.setFont(QFont("Segoe UI", 14, QFont.Bold))
        title.setStyleSheet("color: #ffffff;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # 상태 메시지
        self.status_label = QLabel("필수 구성 요소를 다운로드하고 있습니다...")
        self.status_label.setFont(QFont("Segoe UI", 10))
        self.status_label.setStyleSheet("color: #cccccc;")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setWordWrap(True)
        layout.addWidget(self.status_label)
        
        # 진행률 바
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #444444;
                border-radius: 5px;
                text-align: center;
                background-color: #2a2a2a;
                color: #ffffff;
                font-size: 11px;
                height: 25px;
            }
            QProgressBar::chunk {
                background-color: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 #5F428B, stop:1 #7B5BA3
                );
                border-radius: 4px;
            }
        """)
        layout.addWidget(self.progress_bar)
        
        # 상세 정보
        self.detail_label = QLabel("준비 중...")
        self.detail_label.setFont(QFont("Segoe UI", 9))
        self.detail_label.setStyleSheet("color: #999999;")
        self.detail_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.detail_label)
        
        # 안내 메시지
        info_label = QLabel("잠시만 기다려주세요. 이 작업은 처음 실행 시에만 수행됩니다.")
        info_label.setFont(QFont("Segoe UI", 8))
        info_label.setStyleSheet("color: #777777;")
        info_label.setAlignment(Qt.AlignCenter)
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        
        layout.addStretch()
    
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
            self.status_label.setText(f"{display_name} 다운로드 중...")
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
            self.status_label.setText("초기화 완료!")
            self.detail_label.setText("YT Downloader를 시작합니다...")
            log.info("Initial binary download completed successfully")
        else:
            self.status_label.setText("초기화 실패")
            self.detail_label.setText("다운로드 중 오류가 발생했습니다.")
            log.error("Initial binary download failed")
        
        # 잠시 후 닫기
        from PyQt5.QtCore import QTimer
        QTimer.singleShot(1000 if success else 3000, self.accept)
    
    def exec_(self):
        """다이얼로그 실행 (자동으로 다운로드 시작)"""
        self.start_download()
        return super().exec_()
