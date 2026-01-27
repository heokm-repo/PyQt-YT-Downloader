"""
                    GNU GENERAL PUBLIC LICENSE
                       Version 3, 29 June 2007

 Copyright (C) 2026 Heo KyungMin

 This program is free software: you can redistribute it and/or modify
 it under the terms of the GNU General Public License as published by
 the Free Software Foundation, either version 3 of the License, or
 (at your option) any later version.

 This program is distributed in the hope that it will be useful,
 but WITHOUT ANY WARRANTY; without even the implied warranty of
 MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 GNU General Public License for more details.

 You should have received a copy of the GNU General Public License
 along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

import sys
import os
from PyQt5.QtWidgets import QApplication, QMessageBox

# 로거를 먼저 초기화 (다른 모듈보다 먼저)
try:
    # main.py가 src 폴더 안에 있으므로 현재 디렉토리를 sys.path에 추가
    current_dir = os.path.dirname(os.path.abspath(__file__))
    if current_dir not in sys.path:
        sys.path.insert(0, current_dir)
    from utils.logger import log
except ImportError:
    # logger를 import할 수 없으면 기본 print 사용
    import logging
    log = logging.getLogger("YTDownloader")
    log.error = lambda msg, exc_info=None: print(f"ERROR: {msg}")
    log.warning = lambda msg, exc_info=None: print(f"WARNING: {msg}")
    log.info = lambda msg, exc_info=None: print(f"INFO: {msg}")
    log.debug = lambda msg, exc_info=None: print(f"DEBUG: {msg}")
    log.critical = lambda msg, exc_info=None: print(f"CRITICAL: {msg}")


def check_dependencies():
    """
    필수 라이브러리가 설치되어 있는지 확인합니다.
    Returns:
        tuple: (성공 여부, 누락된 모듈명 또는 None)
    """
    try:
        import requests
        import yt_dlp
        return True, None
    except ImportError as e:
        missing_module = str(e).split("'")[1] if "'" in str(e) else str(e)
        return False, missing_module


def show_error_message(title, text, informative_text=""):
    """
    오류 메시지를 표시합니다. QApplication이 있으면 QMessageBox를, 없으면 print를 사용합니다.
    """
    if QApplication.instance():
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Critical)
        msg.setText(text)
        if informative_text:
            msg.setInformativeText(informative_text)
        msg.setWindowTitle(title)
        msg.exec_()
    else:
        print(f"[{title}] {text}")
        if informative_text:
            print(f"  {informative_text}")


def main():
    """애플리케이션 메인 진입점"""
    app = None  # QApplication 인스턴스 추적
    
    try:
        # PyInstaller로 패키징된 경우를 위한 경로 설정
        if getattr(sys, 'frozen', False):
            # 실행 파일로 패키징된 경우: _MEIPASS를 사용
            application_path = sys._MEIPASS
            # PyInstaller 환경에서는 src 폴더가 _MEIPASS 루트에 있음
            src_path = os.path.join(application_path, 'src')
            if os.path.exists(src_path) and src_path not in sys.path:
                sys.path.insert(0, src_path)
        else:
            # 개발 환경: main.py가 src 폴더 안에 있으므로 현재 디렉토리가 src
            application_path = os.path.dirname(os.path.abspath(__file__))
        
        # 현재 디렉토리(src)를 sys.path에 추가
        if application_path not in sys.path:
            sys.path.insert(0, application_path)
        
        # PyQt5 애플리케이션을 먼저 생성 (QMessageBox 사용을 위해)
        app = QApplication(sys.argv)
        app.setApplicationName("YT Downloader")
        app.setOrganizationName("YTDownloader")
        
        # 의존성 확인 (QApplication 생성 후)
        deps_ok, missing_module = check_dependencies()
        if not deps_ok:
            show_error_message(
                "오류",
                f"필수 라이브러리 '{missing_module}'를 찾을 수 없습니다.",
                "프로그램을 실행하려면 'pip install -r requirements.txt' 명령어를 실행하여 필요한 라이브러리를 설치해주세요."
            )
            sys.exit(1)
        
        # main_window 모듈은 여기서 import하여 순환 참조 방지
        try:
            from gui.windows.main_window import YTDownloaderPyQt5
        except ImportError as e:
            show_error_message(
                "오류",
                "모듈을 불러올 수 없습니다.",
                f"오류: {str(e)}\n\n필요한 모듈이 누락되었을 수 있습니다."
            )
            log.error(f"Import 오류: {e}", exc_info=True)
            sys.exit(1)
        
        # 메인 윈도우 생성
        try:
            window = YTDownloaderPyQt5()
            window.show()
        except Exception as e:
            show_error_message(
                "오류",
                "프로그램을 시작할 수 없습니다.",
                f"오류: {str(e)}"
            )
            log.error(f"윈도우 생성 오류: {e}", exc_info=True)
            sys.exit(1)
        
        # 애플리케이션 실행
        sys.exit(app.exec_())
        
    except Exception as e:
        log.critical(f"치명적 오류: {e}", exc_info=True)
        show_error_message(
            "치명적 오류",
            "치명적인 오류가 발생했습니다.",
            f"오류: {str(e)}"
        )
        sys.exit(1)


if __name__ == "__main__":
    main()
