import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(__file__))
SRC = os.path.join(ROOT, "src")
TEST_APPDATA = os.path.join(ROOT, "tests", ".appdata")
os.makedirs(TEST_APPDATA, exist_ok=True)
os.environ["APPDATA"] = TEST_APPDATA
if SRC not in sys.path:
    sys.path.insert(0, SRC)

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication

from gui.main_window.controls import (
    create_download_button,
    create_empty_state_label,
    create_main_content_layout,
    create_progress_slider,
    create_status_bar,
    create_status_counter_label,
    create_status_label,
    create_status_sort_button,
    create_task_list_section,
    create_title_bar,
    create_title_bar_button,
    create_url_input,
    create_url_input_section,
)
from resources.styles import (
    DOWNLOAD_BUTTON_HEIGHT,
    MIN_DOWNLOAD_BUTTON_WIDTH,
    MIN_STATUS_LABEL_WIDTH,
    PROGRESS_SLIDER_DEFAULT,
    PROGRESS_SLIDER_MAX,
    PROGRESS_SLIDER_MIN,
    STATUS_BAR_HEIGHT,
    STATUS_COUNTER_HORIZONTAL_PADDING,
    STATUS_SORT_BUTTON_HORIZONTAL_PADDING,
    STATUS_SORT_BUTTON_MIN_WIDTH,
    TITLE_BAR_BUTTON_SIZE,
    TITLE_BAR_HEIGHT,
    URL_INPUT_SECTION_HEIGHT,
)


class MainWindowControlsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_create_main_content_layout_returns_widget_and_layout(self):
        controls = create_main_content_layout(
            "background: rgb(1, 2, 3);",
            (1, 2, 3, 4),
            7,
        )

        self.assertEqual(controls.central_widget.objectName(), "CentralWidget")
        self.assertIn("rgb(1, 2, 3)", controls.central_widget.styleSheet())
        self.assertIs(controls.central_widget.layout(), controls.main_layout)
        self.assertEqual(controls.main_layout.spacing(), 7)

        margins = controls.main_layout.contentsMargins()
        self.assertEqual(
            (margins.left(), margins.top(), margins.right(), margins.bottom()),
            (1, 2, 3, 4),
        )

    def test_create_title_bar_returns_frame_and_wired_controls(self):
        calls = []

        controls = create_title_bar(
            "App",
            "background: transparent;",
            "",
            "",
            "",
            lambda: calls.append("minimize"),
            lambda: calls.append("maximize"),
            lambda: calls.append("close"),
        )

        self.assertEqual(controls.frame.height(), TITLE_BAR_HEIGHT)
        self.assertEqual(controls.title_label.text(), "App")
        self.assertEqual(controls.maximize_button.width(), TITLE_BAR_BUTTON_SIZE)

        controls.minimize_button.click()
        controls.maximize_button.click()
        controls.close_button.click()

        self.assertEqual(calls, ["minimize", "maximize", "close"])

    def test_create_url_input_section_returns_frame_and_wired_controls(self):
        calls = []

        controls = create_url_input_section(
            "Paste URL",
            "Download",
            lambda: calls.append("toggle"),
            lambda: calls.append("download"),
            lambda: calls.append("settings"),
        )

        self.assertEqual(controls.frame.height(), URL_INPUT_SECTION_HEIGHT)
        self.assertEqual(controls.url_input.placeholderText(), "Paste URL")
        self.assertEqual(controls.download_button.text(), "Download")

        controls.toggle_button.click()
        controls.download_button.click()
        controls.settings_button.click()

        self.assertEqual(calls, ["toggle", "download", "settings"])

    def test_create_task_list_section_returns_scroll_area_and_empty_label(self):
        controls = create_task_list_section("No tasks")

        self.assertTrue(controls.scroll_area.isHidden())
        self.assertTrue(controls.scroll_area.widgetResizable())
        self.assertEqual(controls.scroll_area.widget(), controls.scroll_content)
        self.assertEqual(controls.empty_label.text(), "No tasks")
        self.assertGreaterEqual(controls.task_layout.count(), 1)

    def test_create_status_bar_returns_frame_and_controls(self):
        controls = create_status_bar("Ready")

        self.assertEqual(controls.frame.height(), STATUS_BAR_HEIGHT)
        self.assertEqual(controls.sort_button.currentKey(), "newest")
        self.assertEqual(controls.status_label.text(), "Ready")
        self.assertEqual(controls.frame.layout().indexOf(controls.status_label), -1)
        self.assertEqual(controls.progress_slider.value(), PROGRESS_SLIDER_DEFAULT)
        self.assertFalse(controls.progress_slider.isEnabled())
        self.assertEqual(controls.counter_label.text(), "0/0")

    def test_create_title_bar_button_sets_fixed_size_and_cursor(self):
        button = create_title_bar_button("mdi.close", "", lambda: None)

        self.assertEqual(button.width(), TITLE_BAR_BUTTON_SIZE)
        self.assertEqual(button.height(), TITLE_BAR_BUTTON_SIZE)
        self.assertEqual(button.cursor().shape(), Qt.PointingHandCursor)
        self.assertFalse(button.icon().isNull())

    def test_create_url_input_sets_placeholder_and_minimum_width(self):
        line_edit = create_url_input("Paste URL", lambda: None)

        self.assertEqual(line_edit.placeholderText(), "Paste URL")
        self.assertGreaterEqual(line_edit.minimumWidth(), 1)

    def test_create_download_button_sets_primary_dimensions(self):
        button = create_download_button("Download", lambda: None)

        self.assertEqual(button.text(), "Download")
        self.assertEqual(button.height(), DOWNLOAD_BUTTON_HEIGHT)
        self.assertEqual(button.minimumWidth(), MIN_DOWNLOAD_BUTTON_WIDTH)

    def test_create_status_label_sets_minimum_width(self):
        label = create_status_label("Ready")

        self.assertEqual(label.text(), "Ready")
        self.assertEqual(label.minimumWidth(), MIN_STATUS_LABEL_WIDTH)

    def test_create_empty_state_label_is_centered(self):
        label = create_empty_state_label("No tasks")

        self.assertEqual(label.text(), "No tasks")
        self.assertEqual(label.alignment(), Qt.AlignCenter)

    def test_create_progress_slider_is_read_only_default(self):
        slider = create_progress_slider()

        self.assertEqual(slider.minimum(), PROGRESS_SLIDER_MIN)
        self.assertEqual(slider.maximum(), PROGRESS_SLIDER_MAX)
        self.assertEqual(slider.value(), PROGRESS_SLIDER_DEFAULT)
        self.assertFalse(slider.isEnabled())

    def test_create_status_sort_button_uses_option_values(self):
        button = create_status_sort_button((("newest", "Newest"), ("status", "Status")))

        expected_width = max(
            STATUS_SORT_BUTTON_MIN_WIDTH,
            button.fontMetrics().boundingRect("Newest").width() + STATUS_SORT_BUTTON_HORIZONTAL_PADDING,
        )
        self.assertEqual(button.width(), expected_width)
        self.assertEqual(len(button.menu().actions()), 2)
        self.assertEqual(button.text(), "Newest")
        self.assertEqual(button.currentKey(), "newest")

        button.menu().actions()[1].trigger()

        self.assertEqual(button.text(), "Status")
        self.assertEqual(button.currentKey(), "status")

    def test_create_status_sort_button_resizes_for_localized_text(self):
        button = create_status_sort_button((("newest", "최신순"), ("oldest", "오래된순")))

        button.menu().actions()[1].trigger()

        expected_width = max(
            STATUS_SORT_BUTTON_MIN_WIDTH,
            button.fontMetrics().boundingRect("오래된순").width() + STATUS_SORT_BUTTON_HORIZONTAL_PADDING,
        )
        self.assertEqual(button.text(), "오래된순")
        self.assertEqual(button.width(), expected_width)

    def test_create_status_counter_label_resizes_to_text(self):
        label = create_status_counter_label("2/5")

        expected_width = (
            label.fontMetrics().boundingRect("2/5").width()
            + STATUS_COUNTER_HORIZONTAL_PADDING
        )
        self.assertEqual(label.text(), "2/5")
        self.assertEqual(label.width(), expected_width)
        self.assertEqual(label.alignment(), Qt.AlignRight | Qt.AlignVCenter)

        label.setText("12/300")

        expected_width = (
            label.fontMetrics().boundingRect("12/300").width()
            + STATUS_COUNTER_HORIZONTAL_PADDING
        )
        self.assertEqual(label.width(), expected_width)


if __name__ == "__main__":
    unittest.main()
