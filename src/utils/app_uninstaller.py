"""
앱 삭제 기능 모듈
Inno Setup 언인스톨러를 통한 앱 삭제
"""

import os
import sys
import subprocess
from utils.logger import log
from constants import APPDATA_DIR_NAME


def uninstall_app():
    """
    앱 완전 삭제 실행 (Inno Setup 언인스톨러 호출)
    
    Returns:
        bool: 성공 여부 (True: 삭제 프로세스 시작, False: 실패)
    """
    try:
        # 개발 환경 체크
        if not getattr(sys, 'frozen', False):
            log.warning("개발 환경에서는 앱 삭제가 시뮬레이션됩니다.")
            return False
        
        # 설치 폴더에서 Inno Setup 언인스톨러 찾기
        install_dir = os.path.dirname(sys.executable)
        uninstaller_path = os.path.join(install_dir, "unins000.exe")
        
        if not os.path.exists(uninstaller_path):
            log.error(f"언인스톨러를 찾을 수 없습니다: {uninstaller_path}")
            return False
        
        log.info(f"Inno Setup 언인스톨러 실행: {uninstaller_path}")
        
        # Inno Setup 언인스톨러를 사일런트 모드로 실행
        subprocess.Popen(
            [uninstaller_path, '/SILENT'],
            creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0
        )
        
        log.info("언인스톨러 실행 완료, 앱 종료 예정...")
        return True
        
    except Exception as e:
        log.error(f"앱 삭제 중 오류 발생: {e}", exc_info=True)
        return False
