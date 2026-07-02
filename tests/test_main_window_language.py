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

from gui.main_window.language import (
    DOWNLOAD_BUTTON_WIDTH_PADDING,
    MainWindowLanguageTexts,
    apply_main_window_language,
    update_download_button_text,
)


class FakeRect:
    def __init__(self, width):
        self._width = width

    def width(self):
        return self._width


class FakeFontMetrics:
    def __init__(self, width):
        self.width = width

    def boundingRect(self, text):
        return FakeRect(self.width + len(text))


class FakeLabel:
    def __init__(self):
        self.text = None

    def setText(self, text):
        self.text = text


class FakeInput:
    def __init__(self):
        self.placeholder = None

    def setPlaceholderText(self, text):
        self.placeholder = text


class FakeButton:
    def __init__(self):
        self._text = ""
        self.minimum_width = None

    def setText(self, text):
        self._text = text

    def text(self):
        return self._text

    def fontMetrics(self):
        return FakeFontMetrics(10)

    def setMinimumWidth(self, width):
        self.minimum_width = width


class FakeWindow:
    def __init__(self):
        self.title = None
        self.app_title_label = FakeLabel()
        self.url_input = FakeInput()
        self.download_btn = FakeButton()
        self.empty_label = FakeLabel()
        self.status_label = FakeLabel()

    def setWindowTitle(self, title):
        self.title = title


class MainWindowLanguageTests(unittest.TestCase):
    def test_update_download_button_text_sets_text_and_minimum_width(self):
        button = FakeButton()

        width = update_download_button_text(button, "Download")

        self.assertEqual(button.text(), "Download")
        self.assertEqual(width, 10 + len("Download") + DOWNLOAD_BUTTON_WIDTH_PADDING)
        self.assertEqual(button.minimum_width, width)

    def test_apply_main_window_language_updates_existing_controls_without_tasks(self):
        window = FakeWindow()
        texts = MainWindowLanguageTexts(
            title="App",
            url_placeholder="Paste URL",
            download_text="Download",
            empty_text="No tasks",
            ready_text="Ready",
        )

        apply_main_window_language(window, texts, has_tasks=False)

        self.assertEqual(window.title, "App")
        self.assertEqual(window.app_title_label.text, "App")
        self.assertEqual(window.url_input.placeholder, "Paste URL")
        self.assertEqual(window.download_btn.text(), "Download")
        self.assertEqual(window.empty_label.text, "No tasks")
        self.assertEqual(window.status_label.text, "Ready")

    def test_apply_main_window_language_keeps_status_when_tasks_exist(self):
        window = FakeWindow()
        window.status_label.setText("Downloading")
        texts = MainWindowLanguageTexts(
            title="App",
            url_placeholder="Paste URL",
            download_text="Download",
            empty_text="No tasks",
            ready_text="Ready",
        )

        apply_main_window_language(window, texts, has_tasks=True)

        self.assertEqual(window.status_label.text, "Downloading")


if __name__ == "__main__":
    unittest.main()