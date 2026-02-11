"""
로깅 시스템 모듈
print() 대신 로그 파일에 기록하여 배포판(exe)에서도 오류 추적 가능
"""
import logging
import os
import sys
from logging.handlers import RotatingFileHandler
from utils.utils import get_user_data_path
from constants import LOG_FILE_NAME, LOGGER_NAME

def setup_logger():
    """로깅 설정: AppData 폴더에 app.log 파일 생성"""
    log_dir = get_user_data_path()
    log_file = os.path.join(log_dir, LOG_FILE_NAME)

    # 로거 생성
    logger = logging.getLogger(LOGGER_NAME)
    logger.setLevel(logging.DEBUG)
    
    # 이미 핸들러가 설정되어 있으면 중복 방지
    if logger.handlers:
        return logger

    # 포맷 설정 (시간 - 레벨 - 메시지)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', 
                                  datefmt='%Y-%m-%d %H:%M:%S')

    # 파일 핸들러 (용량 1MB 넘으면 새 파일 생성, 최대 3개 보관)
    try:
        file_handler = RotatingFileHandler(
            log_file, 
            maxBytes=1024*1024,  # 1MB
            backupCount=3, 
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    except Exception as e:
        # 파일 핸들러 생성 실패 시 콘솔에만 출력
        print(f"로그 파일 핸들러 생성 실패: {e}")

    # 콘솔 핸들러 (개발 중에만 보이도록)
    if not getattr(sys, 'frozen', False):
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    # 예기치 않은 오류(Crash)도 로그에 남기기 위한 훅 설정
    def handle_exception(exc_type, exc_value, exc_traceback):
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
        logger.critical("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))

    sys.excepthook = handle_exception
    
    return logger

# 전역에서 쓸 수 있게 로거 인스턴스 생성
log = setup_logger()
