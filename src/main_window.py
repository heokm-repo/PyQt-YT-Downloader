import os
from typing import Optional

from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QLineEdit, QPushButton, QLabel, QFrame,
                             QMessageBox, QSlider, QDialog, QScrollArea,
                             QApplication, QShortcut)
from PyQt5.QtCore import Qt, pyqtSlot, QPoint, QEvent
from PyQt5.QtGui import QFont, QKeySequence

from settings_dialog import SettingsDialog, load_settings, save_settings
from workers import PlaylistAnalysisWorker
from utils import validate_url
from url_processor import UrlProcessor
from managers import HistoryManager, TaskManager, DuplicateChecker
from selection_manager import SelectionManager
from context_menu import ContextMenuBuilder
from task_actions import TaskActions
from ui.task_item import TaskWidget
from ui.toggle_button import ToggleButton
from logger import log
import constants  # 동적 언어 문자열을 항상 최신 값으로 사용하기 위해 모듈 자체도 임포트
from constants import (
    TaskStatus,
    WORKER_TERMINATE_WAIT_MS, WORKER_SHUTDOWN_WAIT_MS,
    MAIN_WINDOW_X, MAIN_WINDOW_Y, MAIN_WINDOW_WIDTH, MAIN_WINDOW_HEIGHT,
    TITLE_BAR_BUTTON_SIZE, TOGGLE_BUTTON_SIZE, SETTINGS_BUTTON_SIZE,
    APP_TITLE, APP_TITLE_COLOR, MAIN_LAYOUT_MARGINS, MAIN_LAYOUT_SPACING,
    TITLE_BAR_HEIGHT, TITLE_BAR_MARGINS, TITLE_BAR_SPACING,
    TITLE_BAR_FONT_FAMILY, TITLE_BAR_FONT_SIZE,
    TITLE_BAR_MINIMIZE_BUTTON_TEXT, TITLE_BAR_CLOSE_BUTTON_TEXT,
    KEY_LANGUAGE, DEFAULT_LANGUAGE, change_language,
    URL_INPUT_SECTION_HEIGHT, URL_INPUT_CONTAINER_MARGINS, URL_INPUT_CONTAINER_SPACING,
    URL_INPUT_PLACEHOLDER, URL_INPUT_HEIGHT, URL_INPUT_FONT_FAMILY, URL_INPUT_FONT_SIZE,
    DOWNLOAD_BUTTON_TEXT, DOWNLOAD_BUTTON_HEIGHT, DOWNLOAD_BUTTON_WIDTH,
    DOWNLOAD_BUTTON_FONT_FAMILY, DOWNLOAD_BUTTON_FONT_SIZE,
    SETTINGS_BUTTON_TEXT, SETTINGS_BUTTON_FONT_FAMILY, SETTINGS_BUTTON_FONT_SIZE,
    TASK_LIST_MARGINS, TASK_LIST_SPACING, EMPTY_STATE_MESSAGE,
    EMPTY_STATE_FONT_FAMILY, EMPTY_STATE_FONT_SIZE,
    STATUS_BAR_HEIGHT, STATUS_BAR_MARGINS, STATUS_BAR_SPACING,
    STATUS_BAR_DEFAULT_TEXT, STATUS_BAR_FONT_FAMILY, STATUS_BAR_FONT_SIZE,
    PROGRESS_SLIDER_MIN, PROGRESS_SLIDER_MAX, PROGRESS_SLIDER_DEFAULT,
    STATUS_TEXT_WAITING, STATUS_TEXT_WAITING_DOTS, STATUS_TEXT_PAUSED_SAVED, STATUS_TEXT_PREVIOUS_FAILED,
    MSG_READY, MSG_SMART_PASTE_STARTED, MSG_DOWNLOAD_ENABLED, MSG_DOWNLOAD_PAUSED,
    MSG_DOWNLOAD_CANCELLED, MSG_ADDED_TO_QUEUE, MSG_PLAYLIST_ANALYZING,
    MSG_PLAYLIST_REGISTERING, MSG_PLAYLIST_ADDED, MSG_ERROR_COUNT, MSG_COMPLETED_COUNT,
    MSG_NO_NEW_VIDEOS, MSG_PLAYLIST_FETCH_ERROR,
    PLAYLIST_VIDEO_URL_TEMPLATE, PLAYLIST_VIDEO_TITLE_TEMPLATE,
    DIALOG_DUPLICATE_VIDEOS_TITLE, DIALOG_DUPLICATE_VIDEOS_MESSAGE,
    DIALOG_RESUME_DOWNLOAD_TITLE, DIALOG_RESUME_DOWNLOAD_MESSAGE,
    DIALOG_NO_NEW_VIDEOS_TITLE, WARNING_PLAYLIST_WORKER_TIMEOUT
)
from models import DownloadTask
from scheduler import DownloadScheduler
from resources.styles import (
    MAIN_WINDOW_STYLE, CENTRAL_WIDGET_STYLE, TITLE_BAR_STYLE,
    MINIMIZE_BUTTON_STYLE, CLOSE_BUTTON_STYLE, URL_INPUT_CONTAINER_STYLE, URL_INPUT_STYLE,
    DOWNLOAD_BUTTON_STYLE, SETTINGS_BUTTON_STYLE, STATUS_BAR_STYLE,
    STATUS_LABEL_STYLE, PROGRESS_SLIDER_STYLE, EMPTY_LABEL_STYLE
)


class YTDownloaderPyQt5(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # 타이틀 바 제거 (Frameless Window)
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        self.setWindowTitle(APP_TITLE)
        self.setGeometry(MAIN_WINDOW_X, MAIN_WINDOW_Y, MAIN_WINDOW_WIDTH, MAIN_WINDOW_HEIGHT) 
        self.setStyleSheet(MAIN_WINDOW_STYLE)
        
        # 윈도우 이동 변수
        self.oldPos = None
        
        # 데이터 초기화
        self.tasks: list[DownloadTask] = []
        self.task_widgets = {}  # task_id -> TaskWidget 매핑
        self.total_tasks_in_queue = 0
        self.playlist_worker = None  # 플레이리스트 분석 워커
        self.settings = load_settings()
        self.toggle_enabled = True
        
        # 선택 관리
        self.selection_manager = SelectionManager()
        self.context_menu_builder = ContextMenuBuilder(self)
        self.task_actions = TaskActions(self)
        self._click_deselect_targets = []  # 클릭 시 선택 해제할 컨테이너 목록
        
        # 매니저 초기화
        self.history_manager = HistoryManager()
        self.task_manager = TaskManager()
        self.duplicate_checker = DuplicateChecker(self.history_manager, self)
        
        # 다운로드 스케줄러 초기화
        self.scheduler = DownloadScheduler(self)
        self.scheduler.progress_updated.connect(self.on_progress_updated)
        self.scheduler.download_finished.connect(self.on_download_finished)
        self.scheduler.task_started.connect(self.on_task_started)
        self.scheduler.metadata_fetched.connect(self.on_metadata_fetched)
        
        # 언어 설정 적용 (UI 생성 전에 상수 업데이트)
        lang = self.settings.get(KEY_LANGUAGE, DEFAULT_LANGUAGE)
        change_language(lang)

        self.setup_ui()
        # 생성된 UI에 현재 언어 문자열 적용
        self.apply_language_to_ui()
        self.center_window()
        
        # 스마트 Ctrl+V 단축키 설정
        self.paste_shortcut = QShortcut(QKeySequence.Paste, self)
        self.paste_shortcut.activated.connect(self.handle_smart_paste)
        
        # Ctrl+A 전체 선택 단축키 설정
        self.select_all_shortcut = QShortcut(QKeySequence.SelectAll, self)
        self.select_all_shortcut.activated.connect(self.select_all_tasks)
        
        # 이전 작업 목록 불러오기
        self.load_tasks_from_file()
        
        # 스케줄러 초기화 (워커 시작)
        self._initialize_scheduler()

    # --- 헬퍼 메서드 ---
    
    def get_task_by_id(self, task_id: int) -> Optional[DownloadTask]:
        """task_id로 DownloadTask 객체 찾기"""
        return next((t for t in self.tasks if t.id == task_id), None)

    # --- UI 생성 메서드 ---

    def setup_ui(self):
        self.menuBar().hide()
        
        central_widget = QWidget()
        central_widget.setObjectName("CentralWidget")
        central_widget.setStyleSheet(CENTRAL_WIDGET_STYLE)
        self.setCentralWidget(central_widget)
        
        # 전체 레이아웃 (마진 최소화)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(*MAIN_LAYOUT_MARGINS)
        main_layout.setSpacing(MAIN_LAYOUT_SPACING) 
        
        # 1. 커스텀 타이틀 바
        self.create_custom_title_bar(main_layout)
        
        # 2. URL 입력 섹션
        self.create_url_section(main_layout)
        
        # 3. 작업 목록 섹션 (QScrollArea로 변경됨)
        self.create_task_list_section(main_layout)
        
        # 4. 상태 표시줄
        self.create_status_bar(main_layout)

    def apply_language_to_ui(self):
        """현재 언어 설정에 맞게 UI 텍스트를 갱신"""
        # constants 모듈에서 최신 문자열을 직접 읽어와 적용한다.
        # (from constants import ... 으로 가져온 값은 런타임 변경이 반영되지 않기 때문)
        # 타이틀 바
        self.setWindowTitle(constants.APP_TITLE)
        if hasattr(self, "app_title_label"):
            self.app_title_label.setText(constants.APP_TITLE)
        # URL 입력 섹션
        if hasattr(self, "url_input"):
            self.url_input.setPlaceholderText(constants.URL_INPUT_PLACEHOLDER)
        if hasattr(self, "download_btn"):
            self.download_btn.setText(constants.DOWNLOAD_BUTTON_TEXT)
            # 텍스트 길이에 맞춰 버튼 최소 너비를 재조정 (언어별 길이 대응)
            fm = self.download_btn.fontMetrics()
            text_width = fm.boundingRect(self.download_btn.text()).width()
            # 여백/패딩을 고려해 약간 여유를 더해줌
            self.download_btn.setMinimumWidth(text_width + 30)
        # 빈 상태 메시지
        if hasattr(self, "empty_label"):
            self.empty_label.setText(constants.EMPTY_STATE_MESSAGE)
        # 상태바 기본 텍스트 (현재 작업이 없을 때만 갱신)
        if hasattr(self, "status_label") and not self.tasks:
            self.status_label.setText(constants.STATUS_BAR_DEFAULT_TEXT)

    def create_custom_title_bar(self, layout):
        title_frame = QFrame()
        title_frame.setFixedHeight(TITLE_BAR_HEIGHT)
        title_frame.setStyleSheet(TITLE_BAR_STYLE)
        
        title_layout = QHBoxLayout(title_frame)
        title_layout.setContentsMargins(*TITLE_BAR_MARGINS)
        title_layout.setSpacing(TITLE_BAR_SPACING)
        
        # 로고/제목
        self.app_title_label = QLabel(APP_TITLE)
        self.app_title_label.setFont(QFont(TITLE_BAR_FONT_FAMILY, TITLE_BAR_FONT_SIZE, QFont.Bold))
        self.app_title_label.setStyleSheet(f"color: {APP_TITLE_COLOR};")
        title_layout.addWidget(self.app_title_label)
        
        title_layout.addStretch(1)
        
        # 최소화 버튼
        minimize_btn = QPushButton(TITLE_BAR_MINIMIZE_BUTTON_TEXT)
        minimize_btn.setFixedSize(TITLE_BAR_BUTTON_SIZE, TITLE_BAR_BUTTON_SIZE)
        minimize_btn.setCursor(Qt.PointingHandCursor)
        minimize_btn.clicked.connect(self.showMinimized)
        minimize_btn.setStyleSheet(MINIMIZE_BUTTON_STYLE)
        title_layout.addWidget(minimize_btn)
        
        # 닫기 버튼
        close_btn = QPushButton(TITLE_BAR_CLOSE_BUTTON_TEXT)
        close_btn.setFixedSize(TITLE_BAR_BUTTON_SIZE, TITLE_BAR_BUTTON_SIZE)
        close_btn.setCursor(Qt.PointingHandCursor)
        close_btn.clicked.connect(self.close)
        close_btn.setStyleSheet(CLOSE_BUTTON_STYLE)
        title_layout.addWidget(close_btn)
        
        layout.addWidget(title_frame)

    # 윈도우 드래그
    def mousePressEvent(self, event):
        self.setFocus()
        if event.button() == Qt.LeftButton:
            self.oldPos = event.globalPos()
    def mouseMoveEvent(self, event):
        if self.oldPos is not None and event.buttons() == Qt.LeftButton:
            delta = QPoint(event.globalPos() - self.oldPos)
            self.move(self.x() + delta.x(), self.y() + delta.y())
            self.oldPos = event.globalPos()
    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.oldPos = None
    
    def eventFilter(self, source, event):
        """이벤트 필터: 빈 공간 클릭 감지 (스크롤 영역, 상태바)"""
        if event.type() == QEvent.MouseButtonPress and event.button() == Qt.LeftButton:
            # 등록된 컨테이너에서 클릭이 발생했을 때만 선택 해제
            if source in self._click_deselect_targets:
                # 클릭 위치에 TaskWidget이 있는지 확인
                click_pos = event.pos()
                child_at_pos = source.childAt(click_pos)
                
                # 클릭된 위치에 자식 위젯이 없거나, TaskWidget이 아닌 경우에만 선택 해제
                is_card_click = False
                if child_at_pos:
                    # 부모를 따라 올라가며 TaskWidget인지 확인
                    widget = child_at_pos
                    while widget:
                        if widget in self.task_widgets.values():
                            is_card_click = True
                            break
                        widget = widget.parent()
                
                if not is_card_click:
                    self.selection_manager.clear(self.task_widgets)
                    self.setFocus()
        return super().eventFilter(source, event)

    def create_url_section(self, layout):
        input_container = QFrame()
        input_container.setFixedHeight(URL_INPUT_SECTION_HEIGHT)
        input_container.setStyleSheet(URL_INPUT_CONTAINER_STYLE)
        
        container_layout = QHBoxLayout(input_container)
        container_layout.setContentsMargins(*URL_INPUT_CONTAINER_MARGINS)
        container_layout.setSpacing(URL_INPUT_CONTAINER_SPACING)
        
        self.toggle_btn = ToggleButton()
        self.toggle_btn.setFixedSize(TOGGLE_BUTTON_SIZE, TOGGLE_BUTTON_SIZE)
        self.toggle_btn.setCursor(Qt.PointingHandCursor)
        self.toggle_btn.clicked.connect(self.toggle_download)
        container_layout.addWidget(self.toggle_btn)
        
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText(URL_INPUT_PLACEHOLDER)
        self.url_input.setFixedHeight(URL_INPUT_HEIGHT)
        self.url_input.setFont(QFont(URL_INPUT_FONT_FAMILY, URL_INPUT_FONT_SIZE))
        self.url_input.setStyleSheet(URL_INPUT_STYLE)
        self.url_input.returnPressed.connect(self.start_download) # 엔터키 지원
        self.url_input.textChanged.connect(self.on_url_changed)
        container_layout.addWidget(self.url_input, 1)
        
        btn_group = QFrame()
        btn_layout = QHBoxLayout(btn_group)
        btn_layout.setContentsMargins(0, 0, 0, 0)
        btn_layout.setSpacing(0)
        
        self.download_btn = QPushButton(DOWNLOAD_BUTTON_TEXT)
        self.download_btn.setFixedHeight(DOWNLOAD_BUTTON_HEIGHT)
        # 기본 최소 너비만 설정하고, 실제 너비는 텍스트 길이에 따라 동적으로 조정
        self.download_btn.setMinimumWidth(DOWNLOAD_BUTTON_WIDTH)
        self.download_btn.setFont(QFont(DOWNLOAD_BUTTON_FONT_FAMILY, DOWNLOAD_BUTTON_FONT_SIZE, QFont.Bold))
        self.download_btn.setCursor(Qt.PointingHandCursor)
        self.download_btn.clicked.connect(self.start_download)
        self.download_btn.setStyleSheet(DOWNLOAD_BUTTON_STYLE)
        btn_layout.addWidget(self.download_btn)

        self.settings_btn = QPushButton(SETTINGS_BUTTON_TEXT)
        self.settings_btn.setFixedSize(SETTINGS_BUTTON_SIZE, SETTINGS_BUTTON_SIZE)
        self.settings_btn.setFont(QFont(SETTINGS_BUTTON_FONT_FAMILY, SETTINGS_BUTTON_FONT_SIZE))
        self.settings_btn.setCursor(Qt.PointingHandCursor)
        self.settings_btn.clicked.connect(self.open_download_options)
        self.settings_btn.setStyleSheet(SETTINGS_BUTTON_STYLE)
        btn_layout.addWidget(self.settings_btn)
        
        container_layout.addWidget(btn_group)
        
        layout.addWidget(input_container)

    def create_task_list_section(self, layout):
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("background: transparent; border: none;")
        
        self.scroll_content = QWidget()
        self.scroll_content.setStyleSheet("background: transparent;")

        self.scroll_content.installEventFilter(self)
        self._click_deselect_targets.append(self.scroll_content)
        
        self.task_layout = QVBoxLayout(self.scroll_content)
        self.task_layout.setContentsMargins(*TASK_LIST_MARGINS)
        self.task_layout.setSpacing(TASK_LIST_SPACING) # 간격 약간 증가
        
        self.task_layout.addStretch()
        
        self.scroll_area.setWidget(self.scroll_content)
        layout.addWidget(self.scroll_area, 1)
        
        # 빈 상태 라벨
        self.empty_label = QLabel(EMPTY_STATE_MESSAGE)
        self.empty_label.setAlignment(Qt.AlignCenter)
        self.empty_label.setFont(QFont(EMPTY_STATE_FONT_FAMILY, EMPTY_STATE_FONT_SIZE))
        self.empty_label.setStyleSheet(EMPTY_LABEL_STYLE)
        
        layout.addWidget(self.empty_label)
        self.scroll_area.hide()

    def create_status_bar(self, layout):
        status_container = QFrame()
        status_container.setFixedHeight(STATUS_BAR_HEIGHT)
        status_container.setStyleSheet(STATUS_BAR_STYLE)
        
        # 상태바 빈 공간 클릭 감지
        status_container.installEventFilter(self)
        self._click_deselect_targets.append(status_container)
        
        s_layout = QHBoxLayout(status_container)
        s_layout.setContentsMargins(*STATUS_BAR_MARGINS)
        s_layout.setSpacing(STATUS_BAR_SPACING)
        
        self.status_label = QLabel(STATUS_BAR_DEFAULT_TEXT)
        self.status_label.setFont(QFont(STATUS_BAR_FONT_FAMILY, STATUS_BAR_FONT_SIZE))
        self.status_label.setStyleSheet(STATUS_LABEL_STYLE)
        s_layout.addWidget(self.status_label)
        
        self.progress_slider = QSlider(Qt.Horizontal)
        self.progress_slider.setRange(PROGRESS_SLIDER_MIN, PROGRESS_SLIDER_MAX)
        self.progress_slider.setValue(PROGRESS_SLIDER_DEFAULT)
        self.progress_slider.setStyleSheet(PROGRESS_SLIDER_STYLE)
        self.progress_slider.setEnabled(False)
        s_layout.addWidget(self.progress_slider, 1)
        
        layout.addWidget(status_container)


    # --- 키보드 단축키 핸들러 ---
    
    def handle_smart_paste(self):
        """Ctrl+V 핸들러: 입력창 포커스 시 붙여넣기, 그 외에는 자동 다운로드"""
        focused_widget = QApplication.focusWidget()
        if focused_widget == self.url_input:
            self.url_input.paste()
            return

        clipboard = QApplication.clipboard()
        text = clipboard.text().strip()
        
        if text and validate_url(text):
            self.url_input.setText(text)
            self.start_download()
            self.status_label.setText(MSG_SMART_PASTE_STARTED)

    # --- 작업 제어 메서드 (TaskActions로 위임) ---

    def pause_task(self, task_id):
        """개별 작업 일시 정지"""
        self.task_actions.pause_task(task_id)

    def resume_task(self, task_id):
        """일시 정지된 작업을 이어받기"""
        self.task_actions.resume_task(task_id)

    def retry_task(self, task_id):
        """다운로드 재시도"""
        self.task_actions.retry_task(task_id)

    # --- 파일 관련 액션 메서드 (TaskActions로 위임) ---

    def play_file(self, task_id):
        """파일 실행"""
        self.task_actions.play_file(task_id)

    def open_folder(self, task_id):
        """파일이 있는 폴더 열기"""
        self.task_actions.open_folder(task_id)

    def delete_file(self, task_id, confirm=True):
        """파일 삭제 및 목록 제거"""
        self.task_actions.delete_file(task_id, confirm)

    # --- 시그널 연결 ---
    
    def _connect_task_widget_signals(self, task_widget):
        """TaskWidget의 시그널을 메인 윈도우에 연결"""
        task_widget.remove_requested.connect(self.remove_task_from_list)
        task_widget.pause_requested.connect(self.pause_task)
        task_widget.resume_requested.connect(self.resume_task)
        task_widget.retry_requested.connect(self.retry_task)
        task_widget.play_requested.connect(self.play_file)
        task_widget.open_folder_requested.connect(self.open_folder)
        task_widget.delete_file_requested.connect(lambda tid: self.delete_file(tid, True))
        # 선택 및 컨텍스트 메뉴 시그널
        task_widget.clicked.connect(self.on_task_clicked)
        task_widget.right_clicked.connect(self.show_context_menu)

    # --- 선택 관리 메서드 ---
    
    def on_task_clicked(self, task_id, modifiers):
        """카드 클릭 처리 (단일/Shift/Ctrl 선택)"""
        self.selection_manager.handle_click(
            task_id, modifiers, self.task_widgets, self.task_layout
        )
    
    def select_all_tasks(self):
        """모든 작업 선택 (Ctrl+A)"""
        # URL 입력창에 포커스가 있으면 기본 동작 수행
        focused_widget = QApplication.focusWidget()
        if focused_widget == self.url_input:
            self.url_input.selectAll()
            return
        
        # 모든 카드 선택
        self.selection_manager.select_all(self.task_widgets)
    
    def show_context_menu(self, task_id, global_pos):
        """우클릭 컨텍스트 메뉴 표시"""
        # 클릭한 항목이 선택되지 않았으면 해당 항목만 선택
        if not self.selection_manager.is_selected(task_id):
            self.selection_manager.handle_click(task_id, 0, self.task_widgets, self.task_layout)
        
        # 선택된 작업 목록 가져오기
        selected_ids = self.selection_manager.get_selected_ids()
        selected_tasks = [t for t in self.tasks if t.id in selected_ids]
        
        # 콜백 딕셔너리 구성
        callbacks = {
            'play': lambda: self.play_file(selected_ids[0]) if selected_ids else None,
            'open_folder': self._open_folders_for_selected,
            'pause': self._pause_selected_tasks,
            'resume': self._resume_selected_tasks,
            'retry': self._retry_selected_tasks,
            'delete_file': self._delete_files_for_selected,
            'remove': self._remove_selected_from_list,
        }
        
        # 메뉴 빌드 및 표시
        menu = self.context_menu_builder.build(selected_tasks, callbacks)
        menu.exec_(global_pos)
    
    def _pause_selected_tasks(self):
        """선택된 작업들 일시정지"""
        self.task_actions.pause_selected(self.selection_manager.get_selected_ids())
    
    def _resume_selected_tasks(self):
        """선택된 작업들 이어받기"""
        self.task_actions.resume_selected(self.selection_manager.get_selected_ids())
    
    def _retry_selected_tasks(self):
        """선택된 작업들 재시도"""
        task_ids = self.selection_manager.get_selected_ids()
        self.selection_manager.clear(self.task_widgets)
        self.task_actions.retry_selected(task_ids)
    
    def _open_folders_for_selected(self):
        """선택된 작업들의 폴더 열기"""
        self.task_actions.open_folders_for_selected(self.selection_manager.get_selected_ids())
    
    def _delete_files_for_selected(self):
        """선택된 작업들의 파일 삭제"""
        selected_ids = self.selection_manager.get_selected_ids()
        self.selection_manager.clear(self.task_widgets)
        self.task_actions.delete_files_for_selected(selected_ids, self.tasks)
    
    def _remove_selected_from_list(self):
        """선택된 작업들을 목록에서 제거"""
        task_ids = self.selection_manager.get_selected_ids()
        self.selection_manager.clear(self.task_widgets)
        self.task_actions.remove_selected_from_list(task_ids)

    def remove_task_from_list(self, task_id):
        """목록에서 항목 제거 (파일 유지)"""
        widget = self.task_widgets.get(task_id)
        if not widget: return
        
        # 선택 목록에서도 제거
        self.selection_manager.remove_from_selection(task_id)

        self.task_layout.removeWidget(widget)
        widget.deleteLater()
        
        del self.task_widgets[task_id]
        
        self.tasks = [t for t in self.tasks if t.id != task_id]
        
        if not self.task_widgets:
            self.empty_label.show()
            self.scroll_area.hide()
        
        self.update_progress_ui()

    # --- 전체 다운로드 토글 ---

    def update_toggle_button_style(self):
        self.toggle_btn.setPlaying(self.toggle_enabled)

    def toggle_download(self):
        self.toggle_enabled = not self.toggle_enabled
        self.update_toggle_button_style()
        
        if self.toggle_enabled:
            self.status_label.setText(MSG_DOWNLOAD_ENABLED)
            self.scheduler.resume_all()  # 워커 재개
            
            # 전체 일시정지로 인해 일시정지된 작업들을 큐에 다시 추가
            for task in self.tasks:
                if task.status == TaskStatus.PAUSED:
                    # 개별 일시정지 플래그가 설정된 작업은 제외
                    if self.scheduler.is_task_paused(task.id):
                        continue
                    
                    # 작업을 다시 큐에 추가
                    widget = self.task_widgets.get(task.id)
                    if widget:
                        widget.set_status('waiting')
                        widget.status_label.setText(STATUS_TEXT_WAITING_DOTS)
                    
                    task.status = TaskStatus.WAITING
                    
                    # 저장된 settings와 meta 사용
                    settings = task.settings if task.settings else self.settings.copy()
                    meta = task.meta if task.meta else {}
                    
                    # 우선순위 1 (이어받기 작업)로 큐에 추가
                    self.scheduler.add_task(1, task.id, task.url, settings, meta)
            
            self.update_progress_ui()
        else:
            self.status_label.setText(MSG_DOWNLOAD_PAUSED)
            
            # 다운로드 중인 작업들의 상태를 미리 PAUSED로 변경
            # (워커에서 예외 발생 시 올바른 상태로 처리되도록)
            for task in self.tasks:
                if task.status == TaskStatus.DOWNLOADING:
                    task.status = TaskStatus.PAUSED
                    widget = self.task_widgets.get(task.id)
                    if widget:
                        widget.set_paused()
            
            self.scheduler.pause_all()  # 워커 일시정지
            self.update_progress_ui()
        
    def center_window(self):
        screen = self.screen().geometry()
        self.move((screen.width() - self.width()) // 2, (screen.height() - self.height()) // 2)

    def on_url_changed(self):
        self.download_btn.setEnabled(bool(self.url_input.text().strip()))

    # --- 다운로드 시작 및 작업 등록 ---

    def _create_and_register_task(
        self, 
        task_id: int, 
        url: str, 
        video_id: Optional[str] = None,
        title_override: Optional[str] = None
    ) -> DownloadTask:
        """
        TaskWidget 생성 및 작업 등록 (중복 코드 제거)
        
        Args:
            task_id: 작업 ID
            url: 비디오 URL
            video_id: 비디오 ID (선택적)
            title_override: 제목 오버라이드 (선택적, 플레이리스트용)
            
        Returns:
            생성된 DownloadTask 객체
        """
        # TaskWidget 생성
        task_widget = TaskWidget(task_id, url, self)
        if title_override:
            task_widget.title_label.setText(title_override)
        self._connect_task_widget_signals(task_widget)
        
        self.task_layout.insertWidget(0, task_widget)
        self.task_widgets[task_id] = task_widget
        
        # DownloadTask 생성
        current_settings = self.settings.copy()
        task = DownloadTask(
            id=task_id,
            url=url,
            video_id=video_id,
            settings=current_settings
        )
        self.tasks.append(task)
        
        # 스케줄러에 추가 (우선순위 3: 일반 작업)
        self.scheduler.add_task(3, task_id, url, current_settings)
        
        return task

    def _show_task_list(self):
        """작업 목록 UI 표시"""
        if self.scroll_area.isHidden():
            self.empty_label.hide()
            self.scroll_area.show()

    def _handle_playlist_download(self, clean_url: str):
        """플레이리스트 다운로드 처리"""
        # 기존 플레이리스트 워커가 실행 중이면 종료
        if self.playlist_worker and self.playlist_worker.isRunning():
            self.playlist_worker.terminate()
            self.playlist_worker.wait(WORKER_TERMINATE_WAIT_MS)
        
        self.status_label.setText(MSG_PLAYLIST_ANALYZING)
        self.url_input.setEnabled(False)  # 분석 중 입력 비활성화
        self.download_btn.setEnabled(False)
        
        # 플레이리스트 분석 워커 생성 및 시작 (정제된 URL 사용)
        self.playlist_worker = PlaylistAnalysisWorker(clean_url, self)
        self.playlist_worker.analysis_finished.connect(self.on_playlist_analysis_finished)
        self.playlist_worker.start()

    def _handle_single_video_download(self, clean_url: str, video_id: Optional[str]):
        """단일 영상 다운로드 처리"""
        # 중복 다운로드 체크 (큐에 넣기 전에 확인)
        current_settings = self.settings.copy()
        target_format = current_settings.get('format', 'mp4')
        
        if video_id and self.duplicate_checker.check_duplicate(video_id, -1, self.tasks[:], target_format):
            # 사용자가 다시 다운로드하지 않기로 선택한 경우
            self.status_label.setText(MSG_DOWNLOAD_CANCELLED)
            return
        
        # 중복이 아니거나 사용자가 다시 다운로드하기로 선택한 경우
        self.total_tasks_in_queue += 1
        task_id = self.total_tasks_in_queue
        
        # TaskWidget 생성 및 작업 등록
        self._create_and_register_task(task_id, clean_url, video_id)
        
        self.status_label.setText(MSG_ADDED_TO_QUEUE)
        self.update_progress_ui()

    def start_download(self):
        """다운로드 시작 - 오케스트레이션"""
        url = self.url_input.text().strip()
        
        # URL 처리 (검증, 정제, 사용자 선택)
        result = UrlProcessor.process_url(url, self)
        if not result:
            return
        
        self.url_input.clear()
        self._show_task_list()
        
        # 플레이리스트 vs 단일 영상 분기
        if result.is_playlist:
            self._handle_playlist_download(result.clean_url)
        else:
            self._handle_single_video_download(result.clean_url, result.video_id)

    # --- 스케줄러 시그널 핸들러 ---
        
    @pyqtSlot(int)
    def on_task_started(self, task_id):
        widget = self.task_widgets.get(task_id)
        if widget:
            widget.set_started()
            
            # 태스크 상태 업데이트
            task = self.get_task_by_id(task_id)
            if task: task.status = TaskStatus.DOWNLOADING
        
        self.update_progress_ui()

    @pyqtSlot(dict, int)
    def on_progress_updated(self, progress_dict, task_id):
        widget = self.task_widgets.get(task_id)
        if widget:
            widget.update_progress(progress_dict)

    @pyqtSlot(bool, str, int, str)
    def on_download_finished(self, success, message, task_id, final_path):
        widget = self.task_widgets.get(task_id)
        if not widget: return
        
        task = self.get_task_by_id(task_id)
        if task and final_path:
             # 절대 경로로 변환 및 저장
            if not os.path.isabs(final_path):
                final_path = os.path.abspath(final_path)
            task.output_path = final_path

        if success:
            if task: task.status = TaskStatus.FINISHED
            widget.set_finished()
            
            if task:
                # 설정에서 포맷(확장자) 가져오기
                task_format = task.settings.get('format', 'mp4')
                self.history_manager.add_to_history(task.video_id, task.meta, task_format)
        else:
            if message == "일시정지됨":
                # 이미 PAUSED 상태인 경우 (전체 일시정지로 미리 처리됨) - 중복 처리 방지
                if task and task.status == TaskStatus.PAUSED:
                    log.debug(f"Task {task_id}: 이미 일시정지 상태, 중복 처리 스킵")
                    return
                
                # WAITING 상태인 경우 - 재개 중이므로 무시
                if task and task.status == TaskStatus.WAITING:
                    log.info(f"Task {task_id}: 이전 작업의 일시정지 신호 무시됨 (현재 재개 중)")
                    return

                if task: task.status = TaskStatus.PAUSED
                widget.set_paused()
            else:
                if task: task.status = TaskStatus.FAILED
                widget.set_failed(message)
        
        # 워커 정리는 스케줄러가 자동으로 처리
            
        self.update_progress_ui()

    def update_progress_ui(self):
        """상태별 작업 수를 계산하여 UI 업데이트"""
        if not self.tasks:
            self.status_label.setText(MSG_READY)
            return
        
        # 상태별 카운트
        total_tasks = len(self.tasks)  # 전체 작업 수 (실제 존재하는 작업)
        finished_count = 0  # 완료된 작업
        failed_count = 0    # 실패한 작업
        in_progress_count = 0  # 진행 중인 작업 (Waiting, Downloading, Paused)
        
        for task in self.tasks:
            if task.status == TaskStatus.FINISHED:
                finished_count += 1
            elif task.status == TaskStatus.FAILED:
                failed_count += 1
            elif task.is_active():
                in_progress_count += 1
        
        # 오류가 있으면 오류 메시지 표시
        if failed_count > 0:
            msg = MSG_ERROR_COUNT.format(count=failed_count)
        else:
            # 정상 상태: 완료된 작업 수 / 전체 작업 수
            msg = MSG_COMPLETED_COUNT.format(finished=finished_count, total=total_tasks)
        
        self.status_label.setText(msg)

    # --- 설정 관리 ---

    def open_download_options(self):
        """설정 다이얼로그 열기"""
        dialog = SettingsDialog(self.settings.copy(), self)
        if dialog.exec_() == QDialog.Accepted:
            new_settings = dialog.get_new_settings()
            
            old_max = self.settings.get('max_downloads', 3)
            new_max = new_settings.get('max_downloads', 3)
            old_accel = self.settings.get('use_acceleration', False)
            new_accel = new_settings.get('use_acceleration', False)
            
            self.settings = new_settings
            save_settings(self.settings)

            # 언어 변경 반영
            lang = self.settings.get(KEY_LANGUAGE, DEFAULT_LANGUAGE)
            change_language(lang)
            self.apply_language_to_ui()
            
            # 설정 변경 시 동적으로 워커 수 조정
            if old_max != new_max or old_accel != new_accel:
                target_count = 1 if new_accel else new_max
                self.scheduler.adjust_worker_count(target_count)

    def _initialize_scheduler(self):
        """스케줄러 초기화 (워커 시작)"""
        use_acceleration = self.settings.get('use_acceleration', False)
        max_workers = 1 if use_acceleration else int(self.settings.get('max_downloads', 3))
        self.scheduler.initialize(max_workers)
    
    @pyqtSlot(int, dict)
    def on_metadata_fetched(self, task_id, metadata):
        """워커에서 메타데이터를 가져왔을 때 UI 업데이트"""
        widget = self.task_widgets.get(task_id)
        if not widget:
            return
        
        video_id = metadata.get('id')
        
        # UI 카드 업데이트
        widget.update_metadata(metadata)
        
        # tasks 배열의 메타데이터도 업데이트
        for task in self.tasks:
            if task.id == task_id:
                task.meta = metadata
                # video_id가 없으면 추가
                if not task.video_id and video_id:
                    task.video_id = video_id
                break

    # --- 플레이리스트 처리 ---
    
    def _enable_url_input(self):
        """URL 입력창 활성화"""
        self.url_input.setEnabled(True)
        self.download_btn.setEnabled(bool(self.url_input.text().strip()))

    def _handle_playlist_error(self, error_msg: str):
        """플레이리스트 에러 처리"""
        error_text = error_msg if error_msg else MSG_PLAYLIST_FETCH_ERROR
        QMessageBox.warning(self, "플레이리스트 오류", error_text)
        self.status_label.setText(MSG_READY)

    def _filter_duplicate_videos(self, video_ids: list) -> tuple[list, int]:
        """
        중복 비디오 필터링
        
        Returns:
            (filtered_ids, duplicate_count) 튜플
        """
        duplicate_count = 0
        filtered_ids = []
        
        for video_id in video_ids:
            # 히스토리 확인
            if self.history_manager.is_video_downloaded(video_id):
                duplicate_count += 1
                continue
            # 현재 큐 확인
            is_in_queue = any(
                task.video_id == video_id and task.is_active()
                for task in self.tasks
            )
            if is_in_queue:
                duplicate_count += 1
                continue
            filtered_ids.append(video_id)
        
        return filtered_ids, duplicate_count

    def _ask_duplicate_confirmation(self, total_count: int, duplicate_count: int) -> bool:
        """
        중복 영상 제외 확인 다이얼로그
        
        Returns:
            True: 중복 제외, False: 모두 포함
        """
        reply = QMessageBox.question(
            self,
            DIALOG_DUPLICATE_VIDEOS_TITLE,
            DIALOG_DUPLICATE_VIDEOS_MESSAGE.format(total=total_count, duplicate=duplicate_count),
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes
        )
        return reply == QMessageBox.Yes

    def _register_playlist_tasks(self, video_ids: list):
        """플레이리스트 작업들을 등록"""
        # UI 표시 업데이트
        self._show_task_list()
        
        # 각 비디오 ID로 카드 생성 (메타데이터 없이)
        self.status_label.setText(MSG_PLAYLIST_REGISTERING.format(count=len(video_ids)))
        QApplication.processEvents()
        
        for video_id in video_ids:
            self.total_tasks_in_queue += 1
            task_id = self.total_tasks_in_queue
            
            # 비디오 URL 구성
            video_url = PLAYLIST_VIDEO_URL_TEMPLATE.format(video_id=video_id)
            
            # TaskWidget 생성 및 작업 등록
            self._create_and_register_task(
                task_id, 
                video_url, 
                video_id,
                title_override=PLAYLIST_VIDEO_TITLE_TEMPLATE.format(video_id=video_id)
            )
        
        self.status_label.setText(MSG_PLAYLIST_ADDED.format(count=len(video_ids)))
        self.update_progress_ui()

    @pyqtSlot(str, list, bool, str)
    def on_playlist_analysis_finished(self, url, video_ids, success, error_msg):
        """플레이리스트 분석 완료 처리 - 오케스트레이션"""
        self._enable_url_input()
        
        if not success or not video_ids:
            self._handle_playlist_error(error_msg)
            return
        
        # 중복 필터링
        filtered_ids, duplicate_count = self._filter_duplicate_videos(video_ids)
        
        # 중복 발견 시 사용자 확인
        if duplicate_count > 0:
            if self._ask_duplicate_confirmation(len(video_ids), duplicate_count):
                # 중복 제외 (filtered_ids 그대로 사용)
                pass
            else:
                # 모두 포함
                filtered_ids = video_ids
        
        if not filtered_ids:
            QMessageBox.information(self, DIALOG_NO_NEW_VIDEOS_TITLE, MSG_NO_NEW_VIDEOS)
            self.status_label.setText(MSG_READY)
            return
        
        # 작업 등록
        self._register_playlist_tasks(filtered_ids)

    # --- 작업 저장/로드 및 종료 처리 ---

    def load_tasks_from_file(self):
        """저장된 작업 목록 불러오기 및 UI 복원"""
        loaded_tasks = self.task_manager.load_tasks()
        
        if not loaded_tasks:
            return
            
        if self.scroll_area.isHidden():
            self.empty_label.hide()
            self.scroll_area.show()
            
        max_id = 0
        
        for task_data in loaded_tasks:
            # 딕셔너리를 DownloadTask 객체로 변환
            task = DownloadTask.from_dict(task_data)
            
            if task.id > max_id:
                max_id = task.id
            
            # TaskWidget 생성 및 신호 연결
            task_widget = TaskWidget(task.id, task.url, self)
            self._connect_task_widget_signals(task_widget)
            
            self.task_layout.insertWidget(0, task_widget)
            self.task_widgets[task.id] = task_widget
            
            # 메타데이터 기반 UI 채우기
            if task.meta:
                task_widget.update_metadata(task.meta)
            
            # 상태 복원
            if task.status == TaskStatus.FINISHED:
                task_widget.set_finished()
            elif task.status == TaskStatus.PAUSED:
                task_widget.set_paused()
                task_widget.status_label.setText(STATUS_TEXT_PAUSED_SAVED)
                task_widget.percent_label.setText(STATUS_TEXT_WAITING)
            elif task.status == TaskStatus.FAILED:
                task_widget.set_failed(STATUS_TEXT_PREVIOUS_FAILED)
            
            self.tasks.append(task)
        
        # ID 카운터 동기화
        if max_id > self.total_tasks_in_queue:
            self.total_tasks_in_queue = max_id
        self.update_progress_ui()
        
        # 일시정지된 작업이 있는지 확인
        paused_tasks = [task for task in self.tasks if task.status == TaskStatus.PAUSED]
        if paused_tasks:
            # 일시정지된 작업이 있으면 사용자에게 재개 여부 확인
            reply = QMessageBox.question(
                self,
                DIALOG_RESUME_DOWNLOAD_TITLE,
                DIALOG_RESUME_DOWNLOAD_MESSAGE,
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.Yes
            )
            if reply == QMessageBox.Yes:
                # 모든 일시정지된 작업 재개
                for task in paused_tasks:
                    self.resume_task(task.id)

    def closeEvent(self, event):
        # 종료 전 작업 목록 저장
        self.task_manager.save_tasks(self.tasks)
        
        # 플레이리스트 분석 워커 종료
        if self.playlist_worker and self.playlist_worker.isRunning():
            self.playlist_worker.terminate()  # 먼저 종료 신호 전송
            if not self.playlist_worker.wait(WORKER_SHUTDOWN_WAIT_MS):
                log.warning(WARNING_PLAYLIST_WORKER_TIMEOUT)
        
        # 스케줄러 종료 (워커 정리)
        self.scheduler.shutdown()
        
        event.accept()