from PyQt5.QtWidgets import QLabel, QProgressBar, QVBoxLayout
from PyQt5.QtCore import Qt

from gui.widgets.base_dialog import BaseDialog
from resources.styles import STARTUP_DIALOG_WIDTH, STARTUP_DIALOG_HEIGHT, STARTUP_LABEL_STYLE, STARTUP_PROGRESS_STYLE
from constants import APP_TITLE
from locales.strings import STR
from core.workers import StartupWorker


class StartupDialog(BaseDialog):
    """앱 시작 시 표시되는 로딩/초기화 다이얼로그"""
    
    def __init__(self, parent=None):
        super().__init__(
            parent=parent,
            title=STR.TITLE_STARTUP,
            icon_text="🚀",
            show_close_btn=False,  # 진행 중 닫기 방지 (로직상 필요하면 추가)
            show_divider=True
        )
        self.setFixedSize(STARTUP_DIALOG_WIDTH, STARTUP_DIALOG_HEIGHT)
        
        self.worker = None
        self._setup_ui()
        
    def _setup_ui(self):
        # 상태 메시지 라벨
        self.status_label = QLabel(STR.MSG_STARTUP_CHECK_EXT)
        self.status_label.setStyleSheet(STARTUP_LABEL_STYLE)
        self.status_label.setAlignment(Qt.AlignCenter)
        
        # 무한 대기 프로그레스 바 (Indeterminate)
        self.progress_bar = QProgressBar()
        self.progress_bar.setStyleSheet(STARTUP_PROGRESS_STYLE)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setRange(0, 0) # Indeterminate mode
        
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(15)
        layout.addWidget(self.status_label)
        layout.addWidget(self.progress_bar)
        
        self.content_layout.addLayout(layout)
        
    def start_checks(self):
        """백그라운드 체크 시작"""
        self.worker = StartupWorker()
        self.worker.status_updated.connect(self._on_status_updated)
        self.worker.finished_checks.connect(self._on_finished)
        self.worker.error_occurred.connect(self._on_error)
        self.worker.start()
        
    def _on_status_updated(self, msg: str):
        self.status_label.setText(msg)
        
    def _on_finished(self, updates_available: dict, app_update_info: tuple):
        """체크 완료 시 결과를 저장하고 창을 닫음"""
        self.updates_available = updates_available
        self.app_update_info = app_update_info
        
        # '앱 여는 중...' 메시지로 변경 후 지연 시간 없이 닫기
        self.status_label.setText(STR.MSG_STARTUP_OPENING)
        self.accept()
        
    def _on_error(self, err_msg: str):
        # 오류가 나도 로그만 남기고 메인 윈도우로 진입하도록 할 수 있음
        from utils.logger import log
        log.error(f"Startup check error: {err_msg}")
        self.updates_available = {}
        self.app_update_info = (False, None, None)
        self.accept()
        
    def closeEvent(self, event):
        """사용자가 Alt+F4 등으로 닫는 경우 워커 종료"""
        if self.worker and self.worker.isRunning():
            self.worker.quit()
            self.worker.wait()
        super().closeEvent(event)
