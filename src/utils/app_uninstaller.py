"""App uninstall helpers that call the Inno Setup uninstaller."""

import os
import sys
import subprocess
from utils.logger import log
from constants import INNO_UNINSTALL_ARGS, INNO_UNINSTALLER_FILENAME


def uninstall_app():
    """
    Start full app uninstall via the Inno Setup uninstaller.
    
    Returns:
        True if the uninstall process started, False otherwise.
    """
    try:
        # Development-environment check.
        if not getattr(sys, 'frozen', False):
            log.warning("개발 환경에서는 앱 삭제가 시뮬레이션됩니다.")
            return False
        
        # Find the Inno Setup uninstaller in the install directory.
        install_dir = os.path.dirname(sys.executable)
        uninstaller_path = os.path.join(install_dir, INNO_UNINSTALLER_FILENAME)
        
        if not os.path.exists(uninstaller_path):
            log.error(f"언인스톨러를 찾을 수 없습니다: {uninstaller_path}")
            return False
        
        log.info(f"Inno Setup 언인스톨러 실행: {uninstaller_path}")
        
        # Run the Inno Setup uninstaller in silent mode.
        subprocess.Popen(
            [uninstaller_path, *INNO_UNINSTALL_ARGS],
            creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0
        )
        
        log.info("언인스톨러 실행 완료, 앱 종료 예정...")
        return True
        
    except Exception as e:
        log.error(f"앱 삭제 중 오류 발생: {e}", exc_info=True)
        return False
