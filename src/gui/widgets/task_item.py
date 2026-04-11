"""
개별 작업 카드 위젯
"""
import re

from PyQt5.QtWidgets import (QWidget, QFrame, QHBoxLayout, QVBoxLayout, QLabel, 
                             QProgressBar, QPushButton, QSizePolicy)
from PyQt5.QtCore import Qt, pyqtSignal, pyqtSlot, QUrl
from PyQt5.QtGui import QFont, QPixmap, QFontMetrics
from PyQt5.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply

from utils.logger import log
from resources.styles import (
    COLOR_WAITING, COLOR_DOWNLOADING, COLOR_FINISHED, COLOR_ERROR, COLOR_PAUSED,
    get_card_style, THUMBNAIL_LABEL_STYLE, TITLE_LABEL_STYLE, UPLOADER_LABEL_STYLE,
    PROGRESS_BAR_STYLE, PROGRESS_BAR_FINISHED_STYLE, PROGRESS_BAR_ERROR_STYLE,
    PERCENT_LABEL_STYLE, STATUS_LABEL_NORMAL_STYLE, STATUS_LABEL_SUCCESS_STYLE,
    STATUS_LABEL_ERROR_STYLE, STATUS_LABEL_WARNING_STYLE, SIZE_LABEL_STYLE,
    get_action_button_style,
    # Moved Constants
    CARD_HEIGHT, THUMBNAIL_WIDTH, THUMBNAIL_HEIGHT,
    BUTTON_SIZE,
    COLOR_BTN_RED, COLOR_BTN_GREEN, COLOR_BTN_BLUE,
    COLOR_BTN_ORANGE, COLOR_BTN_GRAY
)
from utils.utils import format_bytes
from constants import TaskStatus, MSG_0_PERCENT
from locales.strings import STR

# 상태별 테두리 색상 매핑
STATUS_BORDER_COLORS = {
    TaskStatus.DOWNLOADING: COLOR_DOWNLOADING,
    TaskStatus.FINISHED: COLOR_FINISHED,
    TaskStatus.FAILED: COLOR_ERROR,
    TaskStatus.PAUSED: COLOR_PAUSED,
    TaskStatus.WAITING: COLOR_WAITING,
}


class ElidedLabel(QLabel):
    """공간이 부족하면 텍스트 끝을 ...으로 줄여주는 라벨"""
    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self.full_text = text

    def setText(self, text):
        self.full_text = text
        self.update_text()

    def resizeEvent(self, event):
        self.update_text()
        super().resizeEvent(event)

    def update_text(self):
        # 너비가 0이거나 텍스트가 없으면 리턴
        if self.width() <= 0 or not self.full_text:
            return

        metrics = QFontMetrics(self.font())
        width = self.width()
        
        # 텍스트가 너비보다 작으면 전체 텍스트 표시
        if metrics.width(self.full_text) <= width:
            elided = self.full_text
        else:
            elided = metrics.elidedText(self.full_text, Qt.ElideRight, width)
        
        # 현재 텍스트와 다를 때만 setText 호출 (무한 루프 방지)
        if self.text() != elided:
            super().setText(elided)
            
            # 툴팁은 텍스트가 잘렸을 때만 표시
            if elided != self.full_text:
                self.setToolTip(self.full_text)
            else:
                self.setToolTip("")


class TaskWidget(QFrame):
    """개별 작업 카드 위젯"""
    
    # 신호 정의
    remove_requested = pyqtSignal(int)  # 목록에서 제거 요청
    pause_requested = pyqtSignal(int)  # 일시정지 요청
    resume_requested = pyqtSignal(int)  # 이어받기 요청
    retry_requested = pyqtSignal(int)  # 재시도 요청
    play_requested = pyqtSignal(int)  # 파일 실행 요청
    open_folder_requested = pyqtSignal(int)  # 폴더 열기 요청
    delete_file_requested = pyqtSignal(int)  # 파일 삭제 요청
    clicked = pyqtSignal(int, int)  # 클릭 시그널 (task_id, keyboard_modifiers)
    right_clicked = pyqtSignal(int, object)  # 우클릭 시그널 (task_id, QPoint - global position)
    
    def __init__(self, task_id, url, settings, parent=None):
        super().__init__(parent)
        self.task_id = task_id
        self.url = url
        self.settings = settings
        self.network_manager = QNetworkAccessManager(self)  # 비동기 이미지 다운로드용
        self.network_manager.finished.connect(self.on_thumbnail_downloaded)
        self.pending_reply = None  # 진행 중인 네트워크 요청
        self._selected = False  # 선택 상태
        self._base_border_color = None  # 현재 상태의 기본 테두리 색상
        self.setup_ui()
        self.set_status(TaskStatus.WAITING)
        
    def _get_formatted_title(self, text):
        """제목 앞에 포맷 정보를 추가하여 반환"""
        fmt = self.settings.get('format', 'mp4').upper()
        return f"[{fmt}] {text}"
    
    def setup_ui(self):
        """UI 구성"""
        self.setObjectName("Card")
        self.setFixedHeight(CARD_HEIGHT)
        
        # 기본 상태: 대기 중 (회색 테두리)
        self._update_border(COLOR_WAITING)
        
        root = QHBoxLayout(self)
        root.setContentsMargins(5, 5, 5, 5)
        root.setSpacing(10)

        # 썸네일 (로딩 중)
        self.thumb_label = QLabel(STR.MSG_LOADING)
        self.thumb_label.setFixedSize(THUMBNAIL_WIDTH, THUMBNAIL_HEIGHT)
        self.thumb_label.setStyleSheet(THUMBNAIL_LABEL_STYLE)
        self.thumb_label.setAlignment(Qt.AlignCenter)
        self.thumb_label.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        root.addWidget(self.thumb_label)

        # 정보 영역 (전체 수직 레이아웃)
        info_layout = QVBoxLayout()
        info_layout.setSpacing(0)  # 각 단 간격 0px
        info_layout.setContentsMargins(0, 2, 5, 2)
        
        # === [1단] 상단 컨테이너 (좌측: 텍스트 / 우측: 버튼) ===
        header_container = QHBoxLayout()
        header_container.setSpacing(5)
        
        # 1. 좌측 텍스트 그룹 (제목 + 업로더)
        text_group = QVBoxLayout()
        text_group.setSpacing(0)  # 제목과 업로더 사이 간격 0px
        
        # 제목
        self.title_label = ElidedLabel(self._get_formatted_title(self.url))
        self.title_label.setStyleSheet(TITLE_LABEL_STYLE)
        self.title_label.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        text_group.addWidget(self.title_label)
        
        # 업로더 (채널명)
        self.uploader_label = ElidedLabel(STR.MSG_CHECKING_INFO)
        self.uploader_label.setStyleSheet(UPLOADER_LABEL_STYLE)
        self.uploader_label.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        text_group.addWidget(self.uploader_label)
        
        header_container.addLayout(text_group, 1)  # 텍스트 영역이 남은 공간 차지 (Stretch 1)

        # 2. 우측 버튼 컨테이너
        self.btn_container = QWidget()
        self.btn_container.setStyleSheet("background: transparent; border: none;")
        self.btn_layout = QHBoxLayout(self.btn_container)
        self.btn_layout.setContentsMargins(0, 0, 0, 0)
        self.btn_layout.setSpacing(5)
        self.btn_layout.setAlignment(Qt.AlignRight | Qt.AlignTop)  # 우측 상단 정렬
        
        header_container.addWidget(self.btn_container, 0)  # 버튼 영역은 고정 크기 (Stretch 0)
        
        # 상단 컨테이너를 메인 정보 레이아웃에 추가
        info_layout.addLayout(header_container)
        
        # === [2단] 진행바 ===
        progress_row = QHBoxLayout()
        progress_row.setSpacing(10)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedHeight(6)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setStyleSheet(PROGRESS_BAR_STYLE)
        self.progress_bar.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        progress_row.addWidget(self.progress_bar, 1)
        
        self.percent_label = QLabel(MSG_0_PERCENT)
        self.percent_label.setStyleSheet(PERCENT_LABEL_STYLE)
        self.percent_label.setMinimumWidth(60) 
        self.percent_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.percent_label.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        progress_row.addWidget(self.percent_label)
        
        info_layout.addLayout(progress_row)
        
        # === [3단] 하단 상태 ===
        status_row = QHBoxLayout()
        self.status_label = ElidedLabel(STR.MSG_FETCHING_INFO)
        self.status_label.setStyleSheet(STATUS_LABEL_NORMAL_STYLE)
        self.status_label.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        
        self.size_label = QLabel("")
        self.size_label.setStyleSheet(SIZE_LABEL_STYLE)
        self.size_label.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        
        status_row.addWidget(self.status_label, 1)
        # status_row.addStretch() # 제거: 라벨이 남은 공간을 모두 차지하도록 함
        status_row.addWidget(self.size_label)
        
        info_layout.addLayout(status_row)
        root.addLayout(info_layout)
    
    def _update_border(self, color_hex):
        """카드의 테두리 색상을 변경"""
        self._base_border_color = color_hex
        style = get_card_style(color_hex, self._selected)
        self.setStyleSheet(style)
    
    @property
    def selected(self):
        """선택 상태 반환"""
        return self._selected
    
    @selected.setter
    def selected(self, value):
        """선택 상태 설정"""
        if self._selected != value:
            self._selected = value
            # 현재 테두리 색상으로 스타일 업데이트
            if self._base_border_color:
                style = get_card_style(self._base_border_color, self._selected)
                self.setStyleSheet(style)
    
    def mousePressEvent(self, event):
        """마우스 클릭 이벤트 처리"""
        # 클릭된 위젯이 버튼인지 확인
        clicked_widget = self.childAt(event.pos())
        
        # 버튼이나 버튼의 자식 위젯을 클릭한 경우 카드 클릭 이벤트를 발생시키지 않음
        if clicked_widget:
            # 클릭된 위젯이 버튼인지 확인 (QPushButton 또는 그 부모가 버튼인지)
            widget = clicked_widget
            while widget and widget != self:
                if isinstance(widget, QPushButton):
                    # 버튼 클릭은 버튼 자체가 처리하도록 함
                    super().mousePressEvent(event)
                    return
                widget = widget.parent()
        
        # 버튼이 아닌 영역을 클릭한 경우에만 카드 클릭 이벤트 발생
        if event.button() == Qt.LeftButton:
            # modifiers를 int로 변환하여 전달 (이벤트 객체 수명 문제 방지)
            self.clicked.emit(self.task_id, int(event.modifiers()))
        elif event.button() == Qt.RightButton:
            self.right_clicked.emit(self.task_id, event.globalPos())
        super().mousePressEvent(event)
    
    def create_action_button(self, text, tooltip, callback, color="#555555"):
        """액션 버튼 생성"""
        btn = QPushButton(text)
        btn.setFixedSize(BUTTON_SIZE, BUTTON_SIZE)
        btn.setCursor(Qt.PointingHandCursor)
        btn.setToolTip(tooltip)
        btn.clicked.connect(callback)
        btn.setStyleSheet(get_action_button_style(color))
        return btn
    
    def _get_button_configs(self, state):
        """상태별 버튼 설정 반환"""
        # 버튼 설정: (아이콘, 툴팁, 시그널, 색상)
        # 버튼 설정: (아이콘, 툴팁, 시그널, 색상)
        pause_btn = ("⏸", STR.TOOLTIP_PAUSE, self.pause_requested, COLOR_BTN_RED)
        delete_btn = ("🗑️", STR.TOOLTIP_CANCEL, self.delete_file_requested, COLOR_BTN_RED)
        resume_btn = ("▶", STR.TOOLTIP_RESUME, self.resume_requested, COLOR_BTN_GREEN)
        remove_btn = ("❌", STR.TOOLTIP_REMOVE, self.remove_requested, COLOR_BTN_GRAY)
        play_btn = ("▶", STR.TOOLTIP_PLAY, self.play_requested, COLOR_BTN_GREEN)
        folder_btn = ("📂", STR.TOOLTIP_OPEN_FOLDER, self.open_folder_requested, COLOR_BTN_BLUE)
        file_del_btn = ("🗑️", STR.TOOLTIP_DELETE_FILE, self.delete_file_requested, COLOR_BTN_RED)
        retry_btn = ("↻", STR.TOOLTIP_RETRY, self.retry_requested, COLOR_BTN_ORANGE)
        
        # 상태별 버튼 목록
        button_configs = {
            TaskStatus.DOWNLOADING: [pause_btn, delete_btn],
            TaskStatus.PAUSED: [resume_btn, remove_btn],
            TaskStatus.FINISHED: [play_btn, folder_btn, file_del_btn, remove_btn],
            TaskStatus.FAILED: [retry_btn, remove_btn],
        }
        
        # 기본값: waiting 등
        return button_configs.get(state, [remove_btn])
    
    def update_buttons(self, state):
        """작업 상태에 따라 버튼 패널 갱신"""
        # 기존 버튼 제거
        while self.btn_layout.count():
            item = self.btn_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
        
        # 상태별 버튼 추가
        for icon, tooltip, signal, color in self._get_button_configs(state):
            # 클로저 문제 방지를 위해 람다 내부에서 signal을 직접 참조
            def make_callback(sig):
                return lambda: sig.emit(self.task_id)
            
            btn = self.create_action_button(
                icon, tooltip,
                make_callback(signal),
                color
            )
            self.btn_layout.addWidget(btn)
    
    def set_status(self, status):
        """상태 설정 및 UI 업데이트"""
        self.current_status = status
        
        # 테두리 색상 변경 (딕셔너리 매핑 사용, 기본값: WAITING)
        border_color = STATUS_BORDER_COLORS.get(status, COLOR_WAITING)
        self._update_border(border_color)
        
        # 버튼 업데이트
        self.update_buttons(status)
    
    def update_progress(self, progress_dict):
        """진행률 업데이트"""
        try:
            percent_str = progress_dict.get('_percent_str', '0%')
            percent_clean = re.sub(r'\x1b\[[0-9;]*m', '', percent_str).strip()
            
            self.percent_label.setText(percent_clean)
            try:
                val = float(percent_clean.rstrip('%'))
                self.progress_bar.setValue(int(val))
            except ValueError:
                pass

            downloaded = format_bytes(progress_dict.get('downloaded_bytes', 0))
            total = format_bytes(progress_dict.get('total_bytes') or progress_dict.get('total_bytes_estimate', 0))
            self.size_label.setText(f"{downloaded} / {total}")
            
            status = progress_dict.get('status', '')
            speed = re.sub(r'\x1b\[[0-9;]*m', '', progress_dict.get('_speed_str', '')).strip()
            
            if status == 'postprocessing':
                self.status_label.setText(STR.STATUS_CONVERTING)
            elif speed:
                self.status_label.setText(STR.STATUS_DOWNLOADING_SPEED.format(speed=speed))
            else:
                self.status_label.setText(STR.STATUS_DOWNLOADING_DOTS)
                
            # 다운로드 중 상태로 변경 (아직 변경되지 않았다면)
            if self.current_status != TaskStatus.DOWNLOADING:
                self.set_status(TaskStatus.DOWNLOADING)

        except Exception as e:
            log.error(f"UI 업데이트 오류 (task_id={self.task_id}): {e}", exc_info=True)
    
    def update_metadata(self, meta):
        """메타데이터로 UI 업데이트"""
        title = meta.get('title', '(제목 없음)')
        self.title_label.setText(self._get_formatted_title(title))
        self.uploader_label.setText(meta.get('uploader', 'Unknown'))
        self.status_label.setText(STR.STATUS_WAITING_DOTS)
        
        # 저장된 파일 크기가 있으면 표시 (Persistence 로드)
        if 'file_size' in meta:
            size_str = format_bytes(meta['file_size'])
            self.size_label.setText(size_str)
            # 만약 완료 상태라면 상태 텍스트도 업데이트
            if self.current_status == TaskStatus.FINISHED:
                self.status_label.setText(STR.STATUS_COMPLETED)
        
        # 기존 진행 중인 요청 취소
        if self.pending_reply:
            self.pending_reply.abort()
            self.pending_reply = None
        
        # 썸네일 비동기 다운로드
        thumbnail_url = meta.get('thumbnail')
        if thumbnail_url:
            self.thumb_label.setText(STR.STATUS_WAITING_DOTS)
            url = QUrl(thumbnail_url)
            request = QNetworkRequest(url)
            request.setRawHeader(b'User-Agent', b'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
            self.pending_reply = self.network_manager.get(request)
        else:
            self.thumb_label.setText(STR.STATUS_NO_IMAGE)
    
    @pyqtSlot(QNetworkReply)
    def on_thumbnail_downloaded(self, reply):
        """썸네일 다운로드 완료 처리"""
        if reply != self.pending_reply:
            # 다른 요청의 응답이면 무시
            reply.deleteLater()
            return
        
        self.pending_reply = None
        
        if reply.error() == QNetworkReply.NoError:
            try:
                data = reply.readAll()
                pix = QPixmap()
                if pix.loadFromData(data):
                    pix = pix.scaled(THUMBNAIL_WIDTH, THUMBNAIL_HEIGHT, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
                    self.thumb_label.setPixmap(pix)
                else:
                    self.thumb_label.setText(STR.STATUS_NO_IMAGE)
            except Exception as e:
                log.warning(f"썸네일 로드 실패 (task_id={self.task_id}): {e}", exc_info=True)
                self.thumb_label.setText(STR.STATUS_NO_IMAGE)
        else:
            self.thumb_label.setText(STR.STATUS_NO_IMAGE)
        
        reply.deleteLater()
    
    def set_finished(self, file_size=None):
        """완료 상태로 설정"""
        self.set_status(TaskStatus.FINISHED)
        self.status_label.setText(STR.STATUS_COMPLETED)
        self.status_label.setStyleSheet(STATUS_LABEL_SUCCESS_STYLE)
        self.progress_bar.setStyleSheet(PROGRESS_BAR_FINISHED_STYLE)
        self.progress_bar.setValue(100)
        self.percent_label.setText(MSG_0_PERCENT.replace('0', '100'))
        
        # 파일 크기가 전달되면 단일 값으로 표시
        if file_size is not None:
            self.size_label.setText(format_bytes(file_size))
    
    def set_failed(self, message):
        """실패 상태로 설정"""
        self.set_status(TaskStatus.FAILED)
        self.status_label.setText(STR.STATUS_FAILED_FMT.format(message=message))
        self.status_label.setStyleSheet(STATUS_LABEL_ERROR_STYLE)
        self.progress_bar.setStyleSheet(PROGRESS_BAR_ERROR_STYLE)
    
    def set_paused(self):
        """일시정지 상태로 설정"""
        self.set_status(TaskStatus.PAUSED)
        self.status_label.setText(STR.STATUS_PAUSED)
        self.status_label.setStyleSheet(STATUS_LABEL_WARNING_STYLE)
    
    def set_started(self):
        """다운로드 시작 상태로 설정"""
        self.set_status(TaskStatus.DOWNLOADING)
        self.status_label.setText(STR.STATUS_PREPARING)
