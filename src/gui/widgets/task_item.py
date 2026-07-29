"""Individual task-card widget."""

from PyQt5.QtWidgets import (
    QWidget, QFrame, QHBoxLayout, QVBoxLayout, QLabel, QProgressBar, QPushButton,
)
from PyQt5.QtCore import Qt, pyqtSignal, pyqtSlot, QSize
from PyQt5.QtGui import QPixmap, QFontMetrics
from PyQt5.QtNetwork import QNetworkAccessManager, QNetworkReply
import qtawesome as qta

from utils.logger import log
from resources.styles import (
    get_card_style, THUMBNAIL_LABEL_STYLE, TITLE_LABEL_STYLE, UPLOADER_LABEL_STYLE,
    PROGRESS_BAR_STYLE,
    PERCENT_LABEL_STYLE, STATUS_LABEL_NORMAL_STYLE,
    SIZE_LABEL_STYLE, ACTION_BUTTON_STYLE,
    # Moved Constants
    CARD_HEIGHT, THUMBNAIL_WIDTH, THUMBNAIL_HEIGHT,
    BUTTON_SIZE,
)
from constants import TaskStatus, MSG_0_PERCENT
from gui.tasks.task_button_config import get_task_button_specs
from gui.tasks.task_click_target import is_click_on_child_type
from gui.tasks.task_metadata_display import build_task_metadata_display, format_task_title
from gui.tasks.task_progress_display import build_task_progress_display
from gui.tasks.task_status_style import status_border_color
from gui.tasks.task_thumbnail_request import build_thumbnail_request
from gui.tasks.task_terminal_display import (
    build_failed_display,
    build_finished_display,
    build_paused_display,
    build_started_display,
)
from locales.strings import STR


class ElidedLabel(QLabel):
    """Label that elides overflowing text with an ellipsis."""
    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self.full_text = text

    def setText(self, text):
        self.full_text = text
        self.update_text()

    def resizeEvent(self, event):
        self.update_text()
        super().resizeEvent(event)

    def minimumSizeHint(self):
        # Allow the layout to shrink the label down to 400 px.
        return QSize(400, super().minimumSizeHint().height())

    def update_text(self):
        # Return if width is zero or there is no text.
        if self.width() <= 0 or not self.full_text:
            return

        metrics = QFontMetrics(self.font())
        width = self.width()
        
        # Show the full text when it fits.
        if metrics.width(self.full_text) <= width:
            elided = self.full_text
        else:
            elided = metrics.elidedText(self.full_text, Qt.ElideRight, width)
        
        # Avoid setText loops by updating only when the text changes.
        if self.text() != elided:
            super().setText(elided)
            
            # Show the tooltip only when the text is elided.
            if elided != self.full_text:
                self.setToolTip(self.full_text)
            else:
                self.setToolTip("")


class TaskWidget(QFrame):
    """Individual task-card widget."""
    
    # Signals.
    remove_requested = pyqtSignal(int)  # Request removal from the list.
    pause_requested = pyqtSignal(int)  # Request pause.
    resume_requested = pyqtSignal(int)  # Request resume.
    retry_requested = pyqtSignal(int)  # Request retry.
    play_requested = pyqtSignal(int)  # Request file playback.
    open_folder_requested = pyqtSignal(int)  # Request opening the folder.
    delete_file_requested = pyqtSignal(int)  # Request file deletion.
    clicked = pyqtSignal(int, int)  # Click signal (task_id, keyboard_modifiers).
    right_clicked = pyqtSignal(int, object)  # Context-menu signal (task_id, global QPoint).
    
    def __init__(self, task_id, url, settings, parent=None):
        super().__init__(parent)
        self.task_id = task_id
        self.url = url
        self.settings = settings
        self.network_manager = QNetworkAccessManager(self)  # Used for asynchronous image downloads.
        self.network_manager.finished.connect(self.on_thumbnail_downloaded)
        self.pending_reply = None  # Active network request.
        self._selected = False  # Selection state.
        self._base_border_color = None  # Default border color for the current state.
        self.setup_ui()
        self.set_status(TaskStatus.WAITING)
        
    def _get_formatted_title(self, text):
        """Return a task title prefixed with the selected format."""
        return format_task_title(text, self.settings)
    
    def setup_ui(self):
        """Set up the UI."""
        self._setup_card_frame()
        root = self._create_root_layout()
        root.addWidget(self._create_thumbnail_label())

        info_layout = self._create_info_layout()
        info_layout.addLayout(self._create_header_layout())
        info_layout.addLayout(self._create_progress_row())
        info_layout.addLayout(self._create_status_row())
        root.addLayout(info_layout)

    def _setup_card_frame(self):
        """Apply the fixed card frame properties."""
        self.setObjectName("Card")
        self.setFixedHeight(CARD_HEIGHT)
        self._update_border(status_border_color(TaskStatus.WAITING))

    def _create_root_layout(self):
        root = QHBoxLayout(self)
        root.setContentsMargins(5, 5, 5, 5)
        root.setSpacing(10)
        return root

    def _create_thumbnail_label(self):
        self.thumb_label = QLabel(STR.MSG_LOADING)
        self.thumb_label.setFixedSize(THUMBNAIL_WIDTH, THUMBNAIL_HEIGHT)
        self.thumb_label.setStyleSheet(THUMBNAIL_LABEL_STYLE)
        self.thumb_label.setAlignment(Qt.AlignCenter)
        self.thumb_label.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        return self.thumb_label

    def _create_info_layout(self):
        info_layout = QVBoxLayout()
        info_layout.setSpacing(0)
        info_layout.setContentsMargins(0, 2, 5, 2)
        return info_layout

    def _create_header_layout(self):
        header_container = QHBoxLayout()
        header_container.setSpacing(5)
        header_container.addLayout(self._create_title_text_layout(), 1)
        header_container.addWidget(self._create_button_container(), 0)
        return header_container

    def _create_title_text_layout(self):
        text_group = QVBoxLayout()
        text_group.setSpacing(0)

        self.title_label = ElidedLabel(self._get_formatted_title(self.url))
        self.title_label.setStyleSheet(TITLE_LABEL_STYLE)
        self.title_label.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        text_group.addWidget(self.title_label)

        self.uploader_label = ElidedLabel(STR.MSG_CHECKING_INFO)
        self.uploader_label.setStyleSheet(UPLOADER_LABEL_STYLE)
        self.uploader_label.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        text_group.addWidget(self.uploader_label)
        return text_group

    def _create_button_container(self):
        self.btn_container = QWidget()
        self.btn_container.setStyleSheet("background: transparent; border: none;")
        self.btn_layout = QHBoxLayout(self.btn_container)
        self.btn_layout.setContentsMargins(0, 0, 0, 0)
        self.btn_layout.setSpacing(5)
        self.btn_layout.setAlignment(Qt.AlignRight | Qt.AlignTop)
        return self.btn_container

    def _create_progress_row(self):
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
        return progress_row

    def _create_status_row(self):
        status_row = QHBoxLayout()
        self.status_label = ElidedLabel(STR.MSG_FETCHING_INFO)
        self.status_label.setStyleSheet(STATUS_LABEL_NORMAL_STYLE)
        self.status_label.setAttribute(Qt.WA_TransparentForMouseEvents, True)

        self.size_label = QLabel("")
        self.size_label.setStyleSheet(SIZE_LABEL_STYLE)
        self.size_label.setAttribute(Qt.WA_TransparentForMouseEvents, True)

        status_row.addWidget(self.status_label, 1)
        status_row.addWidget(self.size_label)
        return status_row
    def _update_border(self, color_hex):
        """Change the card border color."""
        self._base_border_color = color_hex
        style = get_card_style(color_hex, self._selected)
        self.setStyleSheet(style)
    
    @property
    def selected(self):
        """Return the selected state."""
        return self._selected
    
    @selected.setter
    def selected(self, value):
        """Set the selected state."""
        if self._selected != value:
            self._selected = value
            # Update style with the current border color.
            if self._base_border_color:
                style = get_card_style(self._base_border_color, self._selected)
                self.setStyleSheet(style)
    
    def mousePressEvent(self, event):
        """Handle task-card mouse clicks."""
        clicked_widget = self.childAt(event.pos())
        if is_click_on_child_type(clicked_widget, self, QPushButton):
            super().mousePressEvent(event)
            return

        if event.button() == Qt.LeftButton:
            self.clicked.emit(self.task_id, int(event.modifiers()))
        elif event.button() == Qt.RightButton:
            self.right_clicked.emit(self.task_id, event.globalPos())
        super().mousePressEvent(event)
    
    def create_action_button(self, icon_name, tooltip, callback, color="#555555"):
        """Create an action button with a QtAwesome icon."""
        btn = QPushButton()
        btn.setFixedSize(BUTTON_SIZE, BUTTON_SIZE)
        btn.setIcon(qta.icon(icon_name, color=color))
        btn.setIconSize(QSize(int(BUTTON_SIZE * 1), int(BUTTON_SIZE * 1)))
        btn.setCursor(Qt.PointingHandCursor)
        btn.setToolTip(tooltip)
        btn.clicked.connect(callback)
        btn.setStyleSheet(ACTION_BUTTON_STYLE)
        return btn
    
    def _signal_for_button_action(self, action):
        """Return the signal used by a task action button."""
        signals = {
            "pause": self.pause_requested,
            "delete_file": self.delete_file_requested,
            "resume": self.resume_requested,
            "remove": self.remove_requested,
            "play": self.play_requested,
            "open_folder": self.open_folder_requested,
            "retry": self.retry_requested,
        }
        return signals[action]
    
    def update_buttons(self, state):
        """Refresh action buttons for the current task status."""
        while self.btn_layout.count():
            item = self.btn_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        for spec in get_task_button_specs(state):
            def make_callback(sig):
                return lambda: sig.emit(self.task_id)

            signal = self._signal_for_button_action(spec.action)
            btn = self.create_action_button(
                spec.icon_name,
                spec.tooltip,
                make_callback(signal),
                spec.color,
            )
            self.btn_layout.addWidget(btn)
    
    def set_status(self, status):
        """Set status and refresh the UI."""
        self.current_status = status
        
        # Change border color from the state map, defaulting to WAITING.
        border_color = status_border_color(status)
        self._update_border(border_color)
        
        # Update buttons.
        self.update_buttons(status)
    
    def update_progress(self, progress_dict):
        """Update progress labels and bar from a yt-dlp progress dictionary."""
        try:
            display = build_task_progress_display(progress_dict)
            self.percent_label.setText(display.percent_text)
            if display.progress_value is not None:
                self.progress_bar.setValue(display.progress_value)
            else:
                log.debug(
                    "Progress percent is not numeric "
                    f"(task_id={self.task_id}, value={display.percent_text})"
                )

            self.size_label.setText(display.size_text)
            self.status_label.setText(display.status_text)

            if self.current_status != TaskStatus.DOWNLOADING:
                self.set_status(TaskStatus.DOWNLOADING)

        except Exception as e:
            log.error(f"UI update error (task_id={self.task_id}): {e}", exc_info=True)
    
    def update_metadata(self, meta):
        """Update metadata labels and start thumbnail loading when available."""
        display = build_task_metadata_display(meta, self.settings)
        self.title_label.setText(display.title_text)
        self.uploader_label.setText(display.uploader_text)
        self.status_label.setText(STR.STATUS_WAITING_DOTS)

        if display.file_size_text is not None:
            self.size_label.setText(display.file_size_text)
            if self.current_status == TaskStatus.FINISHED:
                self.status_label.setText(STR.STATUS_COMPLETED)

        if self.pending_reply:
            self.pending_reply.abort()
            self.pending_reply = None

        if display.thumbnail_url:
            self.thumb_label.setText(STR.STATUS_WAITING_DOTS)
            request = build_thumbnail_request(display.thumbnail_url)
            self.pending_reply = self.network_manager.get(request)
        else:
            self.thumb_label.setText(STR.STATUS_NO_IMAGE)
    
    @pyqtSlot(QNetworkReply)
    def on_thumbnail_downloaded(self, reply):
        """Handle completed thumbnail downloads."""
        if reply != self.pending_reply:
            # Ignore responses for older requests.
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
    
    def _apply_terminal_display(self, display):
        """Apply a terminal task-state display plan to the widget."""
        self.set_status(display.status)
        self.status_label.setText(display.status_text)
        if display.status_style is not None:
            self.status_label.setStyleSheet(display.status_style)
        if display.progress_style is not None:
            self.progress_bar.setStyleSheet(display.progress_style)
        if display.progress_value is not None:
            self.progress_bar.setValue(display.progress_value)
        if display.percent_text is not None:
            self.percent_label.setText(display.percent_text)
        if display.size_text is not None:
            self.size_label.setText(display.size_text)

    def set_finished(self, file_size=None):
        """Set the widget to the completed state."""
        self._apply_terminal_display(build_finished_display(file_size))
    
    def set_failed(self, message):
        """Set the widget to the failed state."""
        self._apply_terminal_display(build_failed_display(message))
    
    def set_paused(self):
        """Set the widget to the paused state."""
        self._apply_terminal_display(build_paused_display())
    
    def set_started(self):
        """Set the widget to the preparing download state."""
        self._apply_terminal_display(build_started_display())
