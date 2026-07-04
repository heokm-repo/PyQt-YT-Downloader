"""Logging system that writes errors to files for packaged exe builds."""
import logging
import os
import sys
from logging.handlers import RotatingFileHandler
from utils.utils import get_user_data_path
from constants import LOG_FILE_NAME, LOGGER_NAME

def setup_logger():
    """Set up logging to app.log under the AppData folder."""
    log_dir = get_user_data_path()
    log_file = os.path.join(log_dir, LOG_FILE_NAME)

    # Create logger.
    logger = logging.getLogger(LOGGER_NAME)
    logger.setLevel(logging.DEBUG)
    
    # Avoid duplicate handlers if already configured.
    if logger.handlers:
        return logger

    # Format: time - level - message.
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', 
                                  datefmt='%Y-%m-%d %H:%M:%S')

    # File handler: rotate after 1 MB and keep up to 3 files.
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
        # Fall back to console output if the file handler cannot be created.
        print(f"로그 파일 핸들러 생성 실패: {e}")

    # Console handler, intended for development.
    if not getattr(sys, 'frozen', False):
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    # Hook unexpected crashes into the log.
    def handle_exception(exc_type, exc_value, exc_traceback):
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
        logger.critical("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))

    sys.excepthook = handle_exception
    
    return logger

# Global logger instance.
log = setup_logger()
