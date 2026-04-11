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
from PyQt5.QtWidgets import QApplication, QMessageBox, QDialog

# 로거를 먼저 초기화 (다른 모듈보다 먼저)
try:
    # main.py가 src 폴더 안에 있으므로 현재 디렉토리를 sys.path에 추가
    current_dir = os.path.dirname(os.path.abspath(__file__))
    if current_dir not in sys.path:
        sys.path.insert(0, current_dir)
    from utils.logger import log
    from locales.strings import STR
    from constants import (
        APP_TITLE, LOGGER_NAME, ORGANIZATION_NAME, SRC_DIR_NAME, REQUIREMENTS_FILENAME
    )
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
        return True, None
    except ImportError as e:
        missing_module = str(e).split("'")[1] if "'" in str(e) else str(e)
        return False, missing_module


def show_error_message(title, text, informative_text=""):
    """
    오류 메시지를 표시합니다. QApplication이 있으면 MessageDialog를, 없으면 print를 사용합니다.
    """
    if QApplication.instance():
        try:
            from gui.widgets.message_dialog import MessageDialog
            import constants
            
            # informative_text가 있으면 text에 붙여서 표시
            full_text = text
            if informative_text:
                full_text += f"\n\n{informative_text}"
                
            dialog = MessageDialog(title, full_text, MessageDialog.ERROR)
            dialog.exec_()
        except ImportError:
            # MessageDialog import 실패 시 폴백
            from PyQt5.QtWidgets import QMessageBox
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
            src_path = os.path.join(application_path, SRC_DIR_NAME)
            if os.path.exists(src_path) and src_path not in sys.path:
                sys.path.insert(0, src_path)
        else:
            # 개발 환경: main.py가 src 폴더 안에 있으므로 현재 디렉토리가 src
            application_path = os.path.dirname(os.path.abspath(__file__))
        
        # 현재 디렉토리(src)를 sys.path에 추가
        if application_path not in sys.path:
            sys.path.insert(0, application_path)
        
        # QtWebEngineWidgets는 QApplication 생성 전에 import 해야 함 (OpenGL 컨텍스트 공유 오류 방지)
        try:
            from PyQt5 import QtWebEngineWidgets  # noqa: F401
        except ImportError:
            pass  # PyQtWebEngine이 없으면 인앱 로그인 기능 비활성화
        
        # PyQt5 애플리케이션을 먼저 생성 (QMessageBox 사용을 위해)
        app = QApplication(sys.argv)
        app.setApplicationName(APP_TITLE)
        app.setOrganizationName(ORGANIZATION_NAME)
        
        # 의존성 확인 (QApplication 생성 후)
        deps_ok, missing_module = check_dependencies()
        if not deps_ok:
            show_error_message(
                STR.TITLE_ERROR,
                STR.ERR_MISSING_DEP.format(module=missing_module),
                STR.MSG_INSTALL_DEP.format(file=REQUIREMENTS_FILENAME)
            )
            sys.exit(1)
        
        # 스타트업 다이얼로그를 통한 바이너리/앱 업데이트 확인
        try:
            from gui.widgets.startup_dialog import StartupDialog
            from utils.bin_manager import check_binaries_exist
            from PyQt5.QtWidgets import QMessageBox
            
            # 설정 로드 및 언어 초기화
            try:
                from gui.windows.settings_dialog import load_settings
                from constants import change_language, KEY_LANGUAGE
                from locales import DEFAULT_LANGUAGE
                
                settings = load_settings()
                lang = settings.get(KEY_LANGUAGE, DEFAULT_LANGUAGE)
                change_language(lang)
                log.info(f"Loaded language early: {lang}")
            except Exception as e:
                log.warning(f"Failed to load language setting early: {e}")
            
            # 앱 시작 로딩 화면 및 백그라운드 업데이트 확인
            startup_dialog = StartupDialog()
            startup_dialog.show()
            startup_dialog.start_checks()
            startup_dialog.exec_()
            
            bin_exist = check_binaries_exist()
            updates = getattr(startup_dialog, 'updates_available', {})
            update_avail, latest_ver, download_url = getattr(startup_dialog, 'app_update_info', (False, None, None))
            
            if not bin_exist:
                # 첫 실행: 사용자에게 언어 선택 및 바이너리 다운로드 확인 (InitSetupDialog 사용)
                from gui.widgets.init_setup_dialog import InitSetupDialog
                from locales import get_language
                from constants import change_language

                # 언어 선택 및 다운로드 확인 대화상자
                setup_dialog = InitSetupDialog()
                
                if setup_dialog.exec_() != QDialog.Accepted:
                    # 사용자가 취소하거나 닫은 경우
                    sys.exit(0)

                # 선택된 언어로 변경 (다이얼로그 내부에서 settings 저장은 됨, 여기선 런타임 적용 확인)
                log.info(f"Initial setup completed. Language: {get_language()}")

                log.info("Binaries not found. Starting initial download...")
                from gui.widgets.download_progress_dialog import DownloadProgressDialog
                
                dialog = DownloadProgressDialog()
                result = dialog.exec_()
                
                if not dialog.download_success:
                    show_error_message(
                        STR.TITLE_INIT_FAIL,
                        STR.ERR_DL_COMPONENT_FAIL,
                        STR.MSG_CHECK_NET
                    )
                    sys.exit(1)
                
                log.info("Initial binary download completed successfully")
            else:
                # 바이너리 업데이트 결과 처리
                if updates:
                    # 업데이트 가능한 항목 표시
                    update_msg = STR.MSG_UPDATE_COMPONENTS
                    for name, info in updates.items():
                        update_msg += f"• {name}: {info['current']} → {info['latest']}\n"
                    update_msg += STR.MSG_UPDATE_ASK_NOW
                    
                    from gui.widgets.message_dialog import MessageDialog
                    import constants
                    
                    dialog = MessageDialog(STR.TITLE_UPDATE_CHECK, update_msg, MessageDialog.QUESTION, show_cancel=False)
                    # QUESTION 타입은 Yes/No 버튼이므로 exec_() 결과가 Accepted(Yes)인지 확인
                    
                    if dialog.exec_() == QDialog.Accepted:
                        log.info("User chose to update binaries")
                        from gui.widgets.download_progress_dialog import DownloadProgressDialog
                        
                        dialog = DownloadProgressDialog(update_mode=True, updates=updates)
                        dialog.exec_()
                        
                        if dialog.download_success:
                            log.info("Update completed successfully")
                        else:
                            log.warning("Update failed or cancelled")
                    else:
                        log.info("User skipped updates")
                else:
                    log.info("All binaries are up to date")

            # ---------------------------------------------------------
            # 앱 자체 업데이트 확인 (App Update Check) 결과 처리
            # ---------------------------------------------------------
            if update_avail:
                try:
                    from utils.app_updater import download_update, apply_update
                    from gui.widgets.message_dialog import MessageDialog
                    import constants
                    
                    msg = STR.MSG_UPDATE_AVAILABLE.format(current=constants.APP_VERSION, latest=latest_ver)
                    dialog = MessageDialog(STR.TITLE_APP_UPDATE, msg, MessageDialog.QUESTION)
                    
                    if dialog.exec_() == QDialog.Accepted:
                        # 다운로드 진행 대화상자
                        from PyQt5.QtWidgets import QProgressDialog
                        from PyQt5.QtCore import Qt
                        
                        progress = QProgressDialog(STR.MSG_UPDATE_DL, STR.BTN_CANCEL, 0, 100)
                        progress.setWindowTitle(STR.TITLE_UPDATE_DL)
                        progress.setWindowModality(Qt.WindowModal)
                        progress.setAutoClose(False)
                        progress.setAutoReset(False)
                        progress.show()
                        
                        def update_progress(pct):
                            progress.setValue(pct)
                            QApplication.processEvents()
                            if progress.wasCanceled():
                                raise Exception("Cancelled by user")
                            
                        # 다운로드 실행
                        new_exe = None
                        try:
                            new_exe = download_update(download_url, update_progress)
                        except Exception as e:
                            log.warning(f"Update download cancelled or failed: {e}")
                        
                        progress.close()
                        
                        if new_exe:
                            if apply_update(new_exe):
                                sys.exit(0)
                            else:
                                show_error_message(STR.TITLE_ERROR, STR.ERR_UPDATE_APPLY)
                        else:
                            pass
                except Exception as e:
                    log.error(f"App update check failed: {e}")

                    
        except Exception as e:
            log.error(f"Binary initialization error: {e}", exc_info=True)
            show_error_message(
                STR.TITLE_INIT_FAIL,
                STR.ERR_INIT_GENERIC,
                f"오류: {str(e)}"
            )
            sys.exit(1)
        
        # main_window 모듈은 여기서 import하여 순환 참조 방지
        try:
            from gui.windows.main_window import YTDownloaderPyQt5
        except ImportError as e:
            show_error_message(
                STR.TITLE_ERROR,
                STR.ERR_MODULE_IMPORT,
                STR.ERR_MODULE_HINT.format(error=str(e))
            )
            log.error(f"Import 오류: {e}", exc_info=True)
            sys.exit(1)
        
        # 메인 윈도우 생성
        try:
            window = YTDownloaderPyQt5()
            window.show()
        except Exception as e:
            show_error_message(
                STR.TITLE_ERROR,
                STR.ERR_START_FAIL,
                f"오류: {str(e)}"
            )
            log.error(f"윈도우 생성 오류: {e}", exc_info=True)
            sys.exit(1)
        
        # 애플리케이션 실행
        sys.exit(app.exec_())
        
    except Exception as e:
        log.critical(f"치명적 오류: {e}", exc_info=True)
        show_error_message(
            STR.TITLE_FATAL,
            STR.ERR_FATAL,
            f"오류: {str(e)}"
        )
        sys.exit(1)


if __name__ == "__main__":
    main()
